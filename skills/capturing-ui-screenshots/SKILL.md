---
name: capturing-ui-screenshots
description: >-
  Captures reproducible evidence screenshots and browser states from web apps in
  Amp orbs with Playwright, mock authentication, mocked APIs, supervised preview
  services, and visual verification. Use when a UI change needs review PNGs,
  browser-state evidence, or reliable Radix Select and AlertDialog captures;
  especially when portal locators detach, overlays animate, or screenshots must
  come from an existing single-worker E2E flow.
license: MIT
metadata:
  author: minpeter
---

# Capturing UI screenshots

Produce reviewable PNG evidence from a deterministic local app state. Build,
serve, check, and capture sequentially; mock every external dependency; inspect
the images; then remove capture-only code and stop the service.

## The invariant

- Use the portal URL only for human review. Playwright runs inside the orb and
  must use the service's private loopback URL from `amp orb service status`.
- Navigate only after installing mock auth and API routes.
- Capture viewport screenshots. Do not use `fullPage`: changing page dimensions
  can alter layout and stale overlay positioning.
- Every assertion waits for a specific state: visible, enabled, exact text, or
  final opacity. A roughly 500 ms delay is allowed only after those waits to let
  a known overlay animation and paint settle.
- Run the build, service checks, Playwright work, and cleanup sequentially. Never
  launch parallel captures.

## 1. Build deterministic E2E state

Read the repository's own scripts and E2E setup first. Use its existing E2E-mode
build and mock-auth contract rather than inventing production credentials. Run
the build by itself and wait for success before starting the preview, for
example:

```bash
pnpm build --mode e2e
```

Adapt the command to the repository. The requirements are an optimized preview
build, E2E/mock-auth mode enabled at build time when the app requires it, and no
concurrent build, server, test, or capture jobs.

If Chromium is missing for the installed Playwright revision, install exactly
that revision through the project dependency before capturing:

```bash
npx playwright install chromium
```

Do not pin a separate Playwright version.

## 2. Start and prove the supervised preview

Start a supervised orb service that consumes Amp's assigned `$PORT`. Keep the
variable expansion inside the service command:

```bash
amp orb service start ui-capture --portal --command 'pnpm preview --host 0.0.0.0 --port "$PORT" --strictPort'
amp orb service status ui-capture
amp orb service logs ui-capture
```

Use the repository's package manager and preview script. Read the assigned port
from service status, then require an HTTP 200 over loopback before Playwright
starts:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:<assigned-port>/
```

The result must be `200`. Diagnose status and logs before retrying. Share the
portal URL with a human reviewer, but do not make internal Playwright traverse
the portal proxy.

## 3. Write one disposable Playwright capture

Prefer a one-shot script over a new test suite. Put it in a temporary,
gitignored location or create a clearly temporary script in the checkout and
delete it after capture. Keep screenshots under `.amp/in/artifacts/`.

Mock authentication before the first navigation with `page.addInitScript`. Mock
network APIs with specific routes and `route.fulfill`; an auth route must match
only `/auth/me`, not invites or another auth subroute. Use reserved
`example.com` names in reusable examples:

```js
import { chromium } from "playwright";

const baseURL = process.env.CAPTURE_BASE_URL;
if (!baseURL) throw new Error("CAPTURE_BASE_URL is required");

const browser = await chromium.launch();
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();

  await page.addInitScript(() => {
    localStorage.setItem(
      "example-auth",
      JSON.stringify({ user: { id: "example-user", email: "you@example.com" } }),
    );
  });

  await page.route(
    /^https:\/\/api\.example\.com\/auth\/me(?:\?.*)?$/,
    (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: "example-user", email: "you@example.com" }),
    }),
  );
  await page.route(
    /^https:\/\/api\.example\.com\/settings\/options(?:\?.*)?$/,
    (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ options: ["Default", "Final option"] }),
    }),
  );

  // Add the app-specific capture sequence from §4 here.
} finally {
  await browser.close();
}
```

Adapt storage keys, response shapes, and endpoint origins to the app. Keep route
regexes anchored and specific. A broad pattern such as `**/auth/**` can swallow
invite subroutes and create misleading UI state.

If captures run inside an existing Playwright suite, preserve serial execution:

```ts
export default defineConfig({
  fullyParallel: false,
  workers: 1,
});
```

Also pass `--workers=1` when the command permits it. Do not add retries to hide
unstable state.

## 4. Capture Radix Select and AlertDialog reliably

Use a helper whose first act is a fresh navigation. The stable sequence is:

1. `page.goto()` the target route and wait for its final app-ready element.
2. Locate the combobox by role and accessible name, scroll it into view, require
   it visible and enabled, then click it.
3. Wait for the final option by role and exact name to be visible. If the app
   exposes transition styles, also wait for the Select content to be opaque.
4. Wait about 500 ms for the known Radix animation and final paint, then take a
   viewport screenshot of the open dropdown.
5. Fresh-navigate to the route again. Re-find every locator; never reuse an
   element handle or locator state from before navigation.
6. Reopen the Select, wait for the exact option, and click it.
7. Click `Apply`, wait for the AlertDialog and its exact warning text to be
   visible, then wait about 500 ms and capture the viewport dialog screenshot.

An adaptable helper looks like this:

```js
async function openFinalOption(page) {
  await page.goto(`${baseURL}/settings`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "Example settings", exact: true })
    .waitFor({ state: "visible" });

  const trigger = page.getByRole("combobox", { name: "Example option" });
  await trigger.scrollIntoViewIfNeeded();
  await trigger.waitFor({ state: "visible" });
  if (!(await trigger.isEnabled())) throw new Error("Select trigger is disabled");
  await trigger.click();

  const option = page.getByRole("option", { name: "Final option", exact: true });
  await option.waitFor({ state: "visible" });
  await page.waitForTimeout(500); // Radix overlay animation and final paint only.
  return option;
}

await openFinalOption(page);
await page.screenshot({ path: ".amp/in/artifacts/select-open.png" });

const option = await openFinalOption(page); // Fresh page state and fresh locators.
await option.click();
await page.getByRole("button", { name: "Apply", exact: true }).click();
const dialog = page.getByRole("alertdialog");
await dialog.waitFor({ state: "visible" });
await dialog.getByText("This change affects current sessions.", { exact: true })
  .waitFor({ state: "visible" });
await page.waitForTimeout(500); // Dialog animation and final paint only.
await page.screenshot({ path: ".amp/in/artifacts/confirm-dialog.png" });
```

Do not keep retrying a detached portal locator. Detachment means the browsing
context or overlay was replaced; repeating the same click indefinitely cannot
repair it.

## 5. Use fallbacks in this order

1. **Fresh page and reopen:** navigate again, reacquire locators, reopen the
   Select, and continue from known state.
2. **Existing passing E2E flow:** inject screenshot calls into an already-passing
   single-worker E2E test rather than rebuilding its setup.
3. **Focused keyboard navigation:** focus the Select trigger, use Arrow keys and
   Enter, and still wait for the exact option/dialog state.
4. **Reduced motion plus final state:** emulate reduced motion, then wait for the
   final overlay to be visible and opaque before a narrowly justified settle.

If those fail, stop and inspect the app state, service logs, route specificity,
and screenshot. Do not respond with unbounded locator retries or parallel workers.

## 6. Verify and clean up

1. Use `view_media` on every PNG. Verify the intended overlay is open, labels
   are legible, no loading/error state is present, and no sensitive data appears.
2. If an image is wrong, change the state preparation or wait and recapture
   sequentially; do not crop away evidence of a bad state.
3. Delete the disposable capture script and any Playwright reports, traces,
   videos, or test-output directories. Keep requested review PNGs only under
   `.amp/in/artifacts/` and never stage them in a product commit.
4. Inspect `git status` and ensure capture scripts, reports, browser artifacts,
   and screenshots are absent from the product diff.
5. Close the browser in `finally`, then stop the supervised service:

```bash
amp orb service stop ui-capture
```

Check service status after stopping it. Cleanup is mandatory: abandoned browsers,
preview servers, workers, and retries consume orb resources and can make later
work unreliable.

## Review checklist

- [ ] E2E/mock-auth build completed before service startup.
- [ ] Supervised preview consumed `$PORT`; status, logs, and HTTP 200 checked.
- [ ] Internal Playwright used loopback; portal reserved for human review.
- [ ] Mock auth installed before navigation; API routes anchored and specific.
- [ ] Captures ran sequentially with one worker and explicit state waits.
- [ ] Select capture used fresh navigation, scroll, open, exact option, settle.
- [ ] Dialog capture fresh-navigated/reopened before select, Apply, exact warning.
- [ ] PNGs are viewport captures under `.amp/in/artifacts/` and were inspected.
- [ ] Temporary code and reports removed; browser and service stopped.
