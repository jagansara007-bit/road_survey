# JavaFX UI Testing Guide

This document outlines the manual verification steps for testing the JavaFX application built in Phase 7.

## Setup
- Start the application in demo mode: `mvn compile javafx:run -Djavafx.args="--demo"`
- Verify that the terminal logs: "Running in DEMO mode. API calls bypassed."

## Map Tab Checklist
- [ ] Map loads successfully using the bundled Leaflet configuration.
- [ ] If internet is disconnected, the map renders a grey background instead of breaking.
- [ ] Mock defect markers appear on the map with varying colours (red for High severity, etc.).
- [ ] Clicking a marker displays a popup with Defect ID and Severity.

## Queue Tab Checklist
- [ ] The priority table displays correctly with the mock data from `fixtures.json`.
- [ ] Adjusting the Budget Slider updates the budget text (the logic for selection will be verified separately).
- [ ] "Export to CSV" button is visible and responsive.

## Verify Tab Checklist
- [ ] The layout correctly displays "Previous Survey" and "Current Survey" sections side-by-side.
- [ ] The control buttons (Mark as Repaired, Mark as Failed, Keep Open) are visible below the images.

## Upload Tab Checklist
- [ ] The form contains fields for Route Name, Survey Date, Video, and GPS track.
- [ ] The progress bar is present and ready for file upload interactions.
