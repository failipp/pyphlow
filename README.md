# pyphlow

This application is being developed as an aid for my personal photography and picture editing workflow. It's supposed to function as a central hub for all actions regarding the workflow.
This ranges from importing the pictures from a camera to exporting the finished photos.

As of now the first step will be to implement a way of viewing the imported pictures and reject all bad photos / duplicates.

## Workflow
My personal (and incomplete) workflow is structured the following way:

### 1: Rejecting photos
It's usually necessary to pick out a few good photos from all the ones that were taken on a shoot.

During this step it will be possible to choose from:
- rejecting the photo completely, which will delete all the files associated with it
- rejecting only the raw file of the photo and keeping the jpeg
- keeping the photo (jpeg and raw)

This step will need two the two directories '1jpeg' and '1raw'. Their names should be explanation enough.

### Further steps
My new workflow isn't quite completed yet. The exact requirements need to be analysed yet.
So far there seem to be three additional steps:
- importing photos (before current step 1)
- editing raw or jpeg photos
- exporting
