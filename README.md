# PowerSS

PowerSS is a screenshot utility for users with multiple monitors. PowerSS allows the user to set up custom keyboard shortcuts for selecting and screenshotting a monitor along with interfaces for compressing and cropping images.

The inspiration for this project came from having a 3440x1440 monitor whose screenshot image sizes were larger than the 8MB file size limit on Discord text chats. PowerSS allows the user to set the max filesize of screenshots and any screenshot whose filesize is larger than the limit is iteratively downscaled to less than the target file size.

# Features

## Screen Capture

Capturing screenshots is the core function of this application. PowerSS allows the user to set a custom keyboard shortcut to capture a screenshot, which will be saved to the desired folder as well as the clipboard. The user can also set the max clipboard size so that the image can be copy-and-pasted to applications with a file size limit. Other features allow for toasts on capture and monitor change. The interface for screen capture also provides a preview section to test which monitor are mapped to which number for selecting.

![Screen capture GUI](http://dpiner.com/projects/CropScreenshot/images/ScreenCapture.png)

## Image Resize

PowerSS also provides the ability to resize existing images to a targeted filesize. This is helpful if the user has an already saved image that is too large for another application. Resizing images is an iterative process where the image is reduced 25% each step until the desired file size is reached. This module also allows the user to preserve the file extension of the file instead of converting to the default PNG file format.

![Image resize GUI](http://dpiner.com/projects/CropScreenshot/images/ResizeImage.png)

## Crop Image

The crop image tab allows the user to capture and save a portion of an existing image. Cropping an image is also an effective way to lower the file size of an image, especially when the user has a high monitor resolution and only a specific portion of a screenshot is important. The image crop application allows the user to save the cropped image as a new file, or to copy it to the clipboard for pasting in another application.

| Original Image                                                                           | Cropped Image                                                                            |
|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| ![Uncropped Image](http://dpiner.com/projects/CropScreenshot/images/CropScreenshot1.png) | ![Uncropped Image](http://dpiner.com/projects/CropScreenshot/images/CropScreenshot2.png) |

## Window Capture

Window capture allows the user to capture a screenshot of a specific window without the need to crop out unwanted screen space. The interface presents the user with a list of available windows and a few options. The user can refresh the list in case a new window has been created, or the can bring the selected window to the front so that it is in focus, and the user can capture a screenshot of the window, which will open in the default image viewer application where the screenshot can be saved. The user can also select the option to return the state of the window. So if the window was minimized, after the screenshot is captured, the window will be minimized again.

![Image resize GUI](http://dpiner.com/projects/CropScreenshot/images/WindowCapture2.png)