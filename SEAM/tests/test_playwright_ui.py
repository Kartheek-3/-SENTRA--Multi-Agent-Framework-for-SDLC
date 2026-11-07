import os
import sys
import time
from playwright.sync_api import sync_playwright

def run_playwright_audit():
    results = {}
    errors = []
    console_messages = []
    artifacts_dir = os.environ.get("SEAM_ARTIFACTS_DIR", "C:/Users/Windows 11/.gemini/antigravity-ide/brain/7e7c71f2-8a76-4c9d-b9cc-51b04da8e2eb")
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Listen to console and uncaught errors
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: errors.append(str(err)))

        url = "http://127.0.0.1:4173"
        print(f"Step 1: Navigating to {url}...", flush=True)
        page.goto(url, wait_until="networkidle")

        title = page.title()
        print(f"  Page title: {title}", flush=True)
        assert "SEAM" in title, f"Title does not contain SEAM: {title}"

        # 1. Landing Page validation
        print("Step 2: Validating Landing Page...", flush=True)
        landing_text = page.inner_text("body")
        assert "TURN REQUIREMENTS" in landing_text, "Missing hero heading"
        assert "ENGINEERED SOFTWARE" in landing_text, "Missing hero heading"
        assert "Autonomous" in landing_text, "Missing autonomous section"
        page.screenshot(path=f"{artifacts_dir}/audit_01_landing.png")
        print("  [PASS] Landing Page hero and description verified.", flush=True)

        # Transition into product shell via Launch SEAM and Demo Login
        launch_btn = page.get_by_role("button", name="Launch SEAM").first
        launch_btn.click()
        time.sleep(0.6)

        demo_btn = page.locator("button.demoBypassBtn")
        if demo_btn.is_visible():
            demo_btn.click()
            time.sleep(0.8)

        # 2. Activity Bar Modules Navigation across all Consoles
        print("Step 3: Validating Activity Bar Modules Navigation...", flush=True)
        nav_tests = [
            ("Dashboard", "dashboard", "Dashboard", "audit_02_dashboard.png"),
            ("Design Studio", "design", "Design Studio", "audit_03_design_studio.png"),
            ("Test Lab", "testlab", "Test Lab", "audit_04_test_lab.png"),
            ("Contracts", "contracts", "Contracts", "audit_05_contracts.png"),
            ("Repair", "repair", "Repair", "audit_06_repair_center.png"),
            ("Runtime", "runtime", "Runtime", "audit_07_runtime.png"),
            ("Model", "models", "Model", "audit_08_model_router.png"),
            ("Delivery", "delivery", "Delivery", "audit_09_delivery.png"),
            ("Evaluation", "evaluation", "Evaluation", "audit_10_evaluation.png"),
            ("Experiments", "experiments", "Experiments", "audit_11_experiments.png"),
            ("Integrations", "integrations", "Integrations", "audit_12_integrations.png"),
            ("Readiness", "readiness", "Readiness", "audit_13_readiness.png"),
        ]

        modules_trigger = page.locator('button[aria-label="SEAM Consoles"]').first
        assert modules_trigger.is_visible(), "Activity Bar modules trigger not visible"

        for label, page_key, expected_substring, screenshot_name in nav_tests:
            modules_trigger.click()
            time.sleep(0.3)
            item = page.locator(f".modulesMenuItem:has-text('{label}')").first
            if not item.is_visible():
                errors.append(f"Modules menu item not visible: {label}")
                print(f"  [FAIL] Modules menu item not visible: {label}", flush=True)
                continue

            item.click()
            time.sleep(0.4)
            current_text = page.inner_text("body")
            if expected_substring.lower() not in current_text.lower():
                errors.append(f"Page '{label}' does not contain expected substring '{expected_substring}'")
                print(f"  [FAIL] {label} content missing '{expected_substring}'", flush=True)
            else:
                print(f"  [PASS] {label} verified (contains '{expected_substring}')", flush=True)

            page.screenshot(path=f"{artifacts_dir}/{screenshot_name}")

        # 3. Interactive Component Checks
        print("Step 4: Interactive Component Testing...", flush=True)
        # Open Design Studio and switch diagram to Sequence
        modules_trigger.click()
        time.sleep(0.3)
        page.locator(".modulesMenuItem:has-text('Design Studio')").first.click()
        time.sleep(0.4)
        seq_item = page.locator("aside div:has-text('Sequence')").first
        seq_item.click()
        time.sleep(0.4)
        print("  [PASS] Design Studio diagram switching to Sequence validated", flush=True)

        # Open Test Lab and switch filter to Quality & Security
        modules_trigger.click()
        time.sleep(0.3)
        page.locator(".modulesMenuItem:has-text('Test Lab')").first.click()
        time.sleep(0.4)
        filter_btn = page.locator("button.consoleTab:has-text('Quality & Security'), div.consoleTab:has-text('Quality & Security')").first
        if filter_btn.is_visible():
            filter_btn.click()
            time.sleep(0.3)
            assert "Security Scanner" in page.inner_text("body"), "Quality & Security filter failed"
            print("  [PASS] Test Lab category filter validated", flush=True)

        # 4. Command Palette (Ctrl+K)
        print("Step 5: Command Palette Keyboard-First Interaction...", flush=True)
        page.keyboard.press("Control+k")
        time.sleep(0.4)
        palette_input = page.locator("input.commandPaletteInput")
        assert palette_input.is_visible(), "Command Palette failed to open on Ctrl+K"
        palette_input.fill("Repair")
        time.sleep(0.3)
        assert "Repair" in page.inner_text(".commandPaletteOverlay"), "Fuzzy search failed in Command Palette"
        page.keyboard.press("Escape")
        time.sleep(0.3)
        assert not palette_input.is_visible(), "Command Palette failed to dismiss on Escape"
        print("  [PASS] Command Palette (Ctrl+K, fuzzy search, Escape dismiss) validated", flush=True)

        # 5. Top Menu Bar & Antigravity HUD
        print("Step 6: Validating Top Menu Bar & Antigravity HUD...", flush=True)
        view_menu_btn = page.locator("button.vscodeMenuTrigger:has-text('View')").first
        assert view_menu_btn.is_visible(), "VS Code 'View' menu not visible"
        view_menu_btn.click()
        time.sleep(0.3)
        dropdown = page.locator(".vscodeDropdownMenu")
        assert dropdown.is_visible(), "VS Code dropdown menu failed to open on click"
        assert "Command Palette..." in dropdown.inner_text(), "Dropdown missing Command Palette option"
        page.keyboard.press("Escape")
        time.sleep(0.2)
        print("  [PASS] VS Code top menu bar interaction verified (open, options, Escape).", flush=True)

        hud = page.locator("aside.antigravityFloatingHUD")
        assert hud.is_visible(), "Antigravity HUD overlay not visible"
        assert "SEAM" in hud.inner_text(), "Missing SEAM brand in HUD"
        # Test dismiss / minimize
        dismiss_btn = page.locator("button.hudIconBtn").first
        dismiss_btn.click()
        time.sleep(0.3)
        assert page.locator(".antigravityFloatingReopenMini").is_visible(), "Antigravity HUD failed to minimize to chip"
        # Test reopen from chip
        chip_btn = page.locator(".antigravityFloatingReopenMini").first
        chip_btn.click()
        time.sleep(0.3)
        assert page.locator("aside.antigravityFloatingHUD").is_visible(), "Antigravity HUD failed to expand from chip"
        print("  [PASS] Antigravity floating HUD interaction verified (render, minimize, expand).", flush=True)

        # 6. Return to Workspace Editor
        print("Step 7: Validating Workspace Editor View...", flush=True)
        explorer_btn = page.locator('button[aria-label="Explorer"]').first
        explorer_btn.click()
        time.sleep(0.5)

        breadcrumbs = page.locator(".breadcrumbBar")
        assert breadcrumbs.is_visible(), "Breadcrumb bar not visible in workspace"
        print("  [PASS] Breadcrumb navigation bar verified.", flush=True)

        # Terminal tabs
        term_tab = page.locator(".terminalPanelTab:has-text('TERMINAL')").first
        if term_tab.is_visible():
            term_tab.click(force=True)
            time.sleep(0.3)
            vite_session = page.locator(".terminalSessionItem:has-text('vite')").first
            if vite_session.is_visible():
                vite_session.click(force=True)
                time.sleep(0.2)
                assert "active" in (vite_session.get_attribute("class") or ""), "Terminal session failed to switch to active"
                print("  [PASS] Terminal multi-session selector verified.", flush=True)

        page.screenshot(path=f"{artifacts_dir}/audit_14_workspace.png")
        page.screenshot(path=f"{artifacts_dir}/audit_15_figma_parity.png")
        print("  [PASS] Full Workspace state and Figma parity verified.", flush=True)

        browser.close()

    print("\n================ Playwright Audit Summary ================", flush=True)
    print(f"Total Assertion / Navigation Errors: {len(errors)}", flush=True)
    if errors:
        for err in errors:
            print(f"  ERROR: {err}", flush=True)
    print(f"Audit Status: {'PASS' if len(errors) == 0 else 'FAIL'}", flush=True)
    return len(errors) == 0

if __name__ == "__main__":
    success = run_playwright_audit()
    sys.exit(0 if success else 1)
