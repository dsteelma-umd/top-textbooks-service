# Sample Tests

## Introduction

This page contains sample tests verify the operation of this application.

## Running the tests

The following assume that the application is running locally (or in a VS Code
Dev Container) on port 5000, and configured to connect to the production
Alma API instance.

See the "[DevelopmentSetup.md](DevelopmentSetup.md)" document for information
about setting up the local development environment.

These tests can also be run against a server running in Kubernetes, with an
appropriate substitution of host names.

## "Happy Path" Tests

The following tests show the nominal operation of the application.

### Single available bib

This test demonstrates operation when a single MMS_ID is provided, and the
item in available, using the MMS ID for "TLC EXTERNAL FLOPPY DISK DRIVE"
(`990062909040108238`):

```zsh
$ export MMS_IDS='["990062909040108238"]'
$ curl -X POST --header "Content-Type: application/json" http://localhost:5000/api/equipment-availability --data $MMS_IDS

{
  "990062909040108238": {
    "count": 1,
    "due": "",
    "status": "available"
  }
}
```

### Unavailable Bib with Future Due Date

The following steps checkout an item in the Primo interface, verifies that
the Equipment Availability application returns the due date for the item, and
then returns the item.

1) Checkout the "TLC EXTERNAL FLOPPY DISK DRIVE" (990062909040108238) item
  in Primo:

    a) Log in to Primo - <https://usmai-umcp.alma.exlibrisgroup.com>, using
       the "SSDR" credentials available in LastPass.

    b) In administrative sidebar on the left side of the page, select
       "Fulfillment | Manage Patron Services". The "Patron Identification"
       page will be displayed.

    c) Enter the id "exl_umcp" for the "TESTER, EXL" test user into the textbox,
       and left-click the "Go" button. The "Patron Services" page will be
       displayed, with the "Loans" tab selected.

    d) In the "Scan item barcode" field, enter the bar code for the
       "TLC EXTERNAL FLOPPY DISK DRIVE" item:

      ```text
      31430051487017
      ```

      Then left-click the "OK" button. The item will be checked out to the
      patron.

2) Run the following commands in a terminal, and verify that output similar to
   that shown is displayed:

   ```zsh
   $ export MMS_IDS='["990062909040108238"]'
   $ curl -X POST --header "Content-Type: application/json" http://localhost:5000/api/equipment-availability --data $MMS_IDS

   {
     "990062909040108238": {
       "count": 0,
       "due": "2024-01-02T20:50:01+00:00",
       "status": "unavailable"
     }
   }
   ```

3) Return the item in the Primo interface by selecting the "Returns" tab on the
   "Patron Services" page, and entering the bar code from the previous steps.

## Error Path Tests

The following tests demonstrate various error conditions.

### Non-existent bib

The following test sends a non-existent MMS_ID.

1) Run the following commands in a terminal, and verify that output similar to
   that shown is displayed:

   ```zsh
   $ export MMS_IDS='["12345"]'
   $ curl -X POST --header "Content-Type: application/json" http://localhost:5000/api/equipment-availability --data $MMS_IDS

   {
     "12345": {
       "count": 0,
       "due": "",
       "status": "nodata"
     }
   }
   ```

### Ignored bibs

The following test shows the output when too many items are requested.

1) Modify the "alma_config.yaml" file, changing the "retrieve_bibs_max_items"
   property to "1" item:

   ```
   retrieve_bibs_max_items: 1
   ```

2) Restart the application.

3) Run the following commands in a terminal, and verify that output similar to
   that shown is displayed:

   ```zsh
   $ export MMS_IDS='["990062909040108238", "990049723650108238"]'
   $ curl -X POST --header "Content-Type: application/json" http://localhost:5000/api/equipment-availability --data $MMS_IDS

   {
     "990049723650108238": {
       "count": 0,
       "due": "",
       "status": "ignored"
     },
     "990062909040108238": {
       "count": 1,
       "due": "",
       "status": "available"
     }
   }
   ```

4) Restore the "alma_config.yaml" file, changing the "retrieve_bibs_max_items"
   property back to "100" items:

   ```
   retrieve_bibs_max_items: 100
   ```

   and restart the application.
