# Arbyte Training Academy

Arbyte Training Academy is an AI-powered embedded-systems learning platform. It provides practical, industry-relevant training and project experience for engineers developing modern embedded and automotive software.

## Learning areas

The academy's course content covers:

- **Automotive Embedded Systems Training** — ECU development, functional safety, security, AUTOSAR fundamentals, Linux, and QNX.
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

Install the Ruby dependencies, then serve the site locally:

	 bundle install
	 bundle exec jekyll serve

Jekyll rebuilds the site when source files change. The generated site is written to `_site`.

## Browser testing

The Playwright checks start a local Jekyll server, verify that each public page loads, and report broken internal links.

The suite is generic and reusable across sites: page names and paths, the base URL, and authentication are all defined in [tests/test_config.py](tests/test_config.py). To point the tests at a different site, edit that file only; `test_site_pages.py` does not need to change.

### CLI mode (default)

From Ubuntu-24.04 WSL, run all checks:

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

