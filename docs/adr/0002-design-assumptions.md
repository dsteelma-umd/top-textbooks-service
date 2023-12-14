# 0002 - Design Assumptions

Date: December 14, 2023

## Context

Documenting the design assumptions for the application provided guidance for
implementing the application, and as a baseline for testing.

It is expected that these assumptions will evolve over time, based on experience
with the application.

## Decision

The following design assumptions were made during initial development:

1) 	Drupal will provide only one "mms_id" for each equipment entry

    In Aleph, equipment was looked up via item barcodes. Barcodes are tied to
    a single physical item, so when there were multiple instances, a barcode for
    each instance was provided.

    In the Alma API items are retrieved by "mms_id", which corresponds to
    a "bib" record. Multiple instances of an item will have different barcodes,
    but will share the same "mms_id".

    Therefore, each equipment entry in Drupal should correspond to a single
    "mms_id", and so it should not be necessary to implement functionality
    to handle multiply "mms_id"s from Drupal.

    Cases where it seems that multiple mms_ids might be necessary are probably
    better handled by making a single "bib" record in Alma.

2) All requested items should have an "AVA" datafield that
   returns "available" or "unavailable"

   Subfield "e" of the "AVA" datafield in the "Retrieve Bibs" endpoint XML
   response has three potential values:

   * available
   * unavailable
   * check_holdings

   The "AVA" datafield itself is optional, and does not appear for all
   items, for reasons which are currently unclear.

   The initial implementation will query the loans for any items:

   * that do not have an "AVA" datafield
   * that have an "AVA" datafield with subfield "e" value of either
     "unavailable" or "check_holdings"

   Ideally, all requested items should have an "AVA" datafield that contains
   either "available" or "unavailable", as a loan query must be performed for
   items individually, which could be time consuming.

3) Drupal with request at most 100 unique mms_ids in a single request

   This reflects a limit of the Alma API, which only allows 100 bib records
   to be returned from the "Retrieve Bibs" endpoint.

   If Drupal requests more 100 unique mms_ids:

   * the application will request the first 100 items and process them normally
   * the response to Drupal will include all mms_ids with the items that were
     ignored returning a status of "ignored"

   Having the application make multiple requests to the Alma API when Drupal
   requests more than 100 mms_ids was considered, but ultimately it such
   functionality was not needed, at least for the initial implementation.

4)	The application will return something for all requested mms_ids, even if
    Alma doesn't return anything for them

    It is possible that Drupal will request the mms_ids of items that are not
    known to Alma. In these cases, the response from the application will
    include those mms_ids, with a status of "no_data"

5) The application will not implement caching of Alma responses, or responses
   to clients. The expectation is that caching can likely be taken care of
   elsewhere, either in Drupal, or using a separate Varnish cache, so it is
   not necessary to complicate the applicaton with caching functionality.

## Consequences

The above assumptions are largely about deferring complexity to a later date,
in the expectation that it will not be needed.

None of the assumptions are irreversible, so we are going to let actual usage
of the application dictate what changes are needed.
