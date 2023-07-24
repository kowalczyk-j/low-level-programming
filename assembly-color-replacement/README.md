## RISC-V sepia color replacement

Replace color of pixels in an image by corresponding sepia tones. The replacement takes place when inequality is satisfied

- 𝒅𝒊𝒔𝒕 ≥ sqrt((𝑹−𝑹𝒔𝒆𝒍)^𝟐 + (𝑮−𝑮𝒔𝒆𝒍)^𝟐 + (𝑩−𝑩𝒔𝒆𝒍)^𝟐)

where (R,G,B) are the values of red, green, blue color components of the pixel, (Rsel,Gsel,Bsel)
are the values of red, green, blue components of selected color (one for the whole image) and
dist is the size of the color neighbourhood.

The formula for calculating of sepia tone of a pixel:
outputRed = (inputRed * .393) + (inputGreen *.769) + (inputBlue * .189)
outputGreen = (inputRed * .349) + (inputGreen *.686) + (inputBlue * .168)
outputBlue = (inputRed * .272) + (inputGreen *.534) + (inputBlue * .131)

If any of these output values is greater than 255, you set it to 255.

### Input
- BMP file containing the source image:
- Sub format: 24 bit RGB – no compression,
- 320x240px,
- file name: “source.bmp”
- (Rsel,Gsel,Bsel) – the values of red, green, blue components (0-255) of the replaced color
(input from keyboard)
- dist - the size (0-442) of the color neighbourhood (input from keyboard)

### Output
- BMP file containing modified image:
- Sub format: 24 bit RGB – no compression,
- 320x240px,
- file name: “source.bmp”