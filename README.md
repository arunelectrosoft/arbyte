# Arbyte

## Browser tests

The Playwright checks start a local Jekyll server, verify each public page loads, and report broken internal links.

The suite is generic and reusable across sites: page names/paths, the base URL, and authentication are all defined in [tests/test_config.py](tests/test_config.py). To point the tests at a different site, edit that file only — `test_site_pages.py` itself does not need to change.

### CLI mode (default)

From Ubuntu-24.04 WSL, run all checks:

	./tests/run_playwright_tests.sh all

Run the checks for one or more pages:

	./tests/run_playwright_tests.sh about
	./tests/run_playwright_tests.sh home,contact

On Windows, use the batch script instead:

	tests\run_playwright_tests.bat all

Page names are whatever keys are defined in `PAGE_PATHS` inside [tests/test_config.py](tests/test_config.py) (`home`, `courses`, `demos`, `blog`, `about`, `contact` by default).

### GUI mode

Pass `--gui` to open a checkbox dialog for picking pages instead of specifying them on the command line:

	./tests/run_playwright_tests.sh --gui
	tests\run_playwright_tests.bat --gui

