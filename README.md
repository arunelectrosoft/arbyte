# Arbyte Training Academy

Arbyte Training Academy is an AI-powered embedded-systems learning platform. It provides practical, industry-relevant training and project experience for engineers developing modern embedded and industry ready software.

## Learning areas

The academy's course content covers:

- **Industrial Embedded Control Systems** — Electronic Control Unit (ECU) development, functional safety, security, AUTOSAR fundamentals, Linux, and QNX.
- **Embedded systems** — microcontrollers, embedded Linux, connectivity, secure boot, firmware-over-the-air updates, and engineering practices.
- **Zephyr RTOS and Edge AI** — real-time development with Zephyr RTOS, Raspberry Pi, Linux, AI, and Edge AI.

The site also presents technical demonstrations, including an intelligent single-phase inverter that explores real-time sensing, control, protection handling, and AC power-conversion monitoring.

## Website

This repository contains the source for the Arbyte Training Academy website, built with Jekyll and published through GitHub Pages.

| Section | Purpose |
|--------|---------|
| Home | Introduces the training academy and its learning focus. |
| Courses | Lists hands-on Linux based embedded build systems, embedded-systems, and Zephyr RTOS/Edge AI training. |
| Demos | Showcases practical embedded and power-electronics demonstrations. |
| Blog | Provides academy updates and technical content. |
| About | Describes the academy mission and industry-focused approach. |
| Contact | Provides a way to get in touch with the academy. |

Page content is maintained in the `siteContents` collections. Layouts are in `_layouts`, reusable page elements are in `_includes`, and site navigation is configured in `_data/navigation.yml`.

## Local development

Install the Ruby dependencies, then serve the site locally from the repository
root. On Ubuntu-24.04 WSL, use the launcher below; it supplies the correct
source/config paths and disables the unreliable `/mnt` filesystem watcher:

	bundle install
	./serve_site.sh

The generated site is written to `_site`. Restart the launcher after editing
source files because WSL file watching is disabled deliberately.

Do not run `bundle exec jekyll server` from `tests/`. Jekyll otherwise treats
that folder as the site source (`Configuration file: none`) and serves test
artifacts instead of the website. It may also crash while watching the
`tests/.venv/lib` and `tests/.venv/lib64` links as the same directory.

## Browser testing

For routine local work, run the compact smoke suite. It reuses a healthy local
server when available (or starts one temporarily), checks all public pages,
internal links, horizontal overflow, core Mermaid/card/footer rendering, and
basic browser security. It then refreshes desktop/mobile screenshots under
`tests/reports/` using `tests/visual_check.py`:

	./tests/run_playwright_basic_tests.sh

Use the comprehensive suite only when a full regression pass is needed. It
starts a local Jekyll server, verifies every public page, and performs detailed
diagram, placeholder, contact, footer, link, image, and security checks.

The suite is generic and reusable across sites: page names and paths, the base URL, and authentication are all defined in [tests/test_config.py](tests/test_config.py). To point the tests at a different site, edit that file only; `test_site_pages.py` does not need to change.

### CLI mode (default)

From Ubuntu-24.04 WSL, run all comprehensive checks:

	./tests/run_playwright_tests.sh all

Run the checks for one or more pages:

	./tests/run_playwright_tests.sh about
	./tests/run_playwright_tests.sh home,contact

On Windows, use the batch script instead:

	tests\run_playwright_tests.bat all

Page names are the keys defined in `PAGE_PATHS` in [tests/test_config.py](tests/test_config.py): `home`, `courses`, `demos`, `blog`, `about`, and `contact` by default.

### GUI mode

Pass `--gui` to open a checkbox dialog for selecting pages instead of specifying them on the command line:

	./tests/run_playwright_tests.sh --gui
	tests\run_playwright_tests.bat --gui

