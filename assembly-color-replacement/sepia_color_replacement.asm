#-------------------------------------------------------------------------------
#author: Jakub Kowalczyk
#date : 2022.05.26
#description : RISC V program for replacing colors of a BMP file in sepia tones
#-------------------------------------------------------------------------------

.eqv ImgInfo_fname	0	#filename ptr
.eqv ImgInfo_hdrdat 	4	#header ptr
.eqv ImgInfo_imdat	8	#first pixel ptr
.eqv ImgInfo_width	12
.eqv ImgInfo_height	16
.eqv ImgInfo_lbytes	20	#size of image line in bytes

.eqv MAX_IMG_SIZE 	230400 # 320 x 240 x 3 (pixels) 

.eqv BMPHeader_Size 54
.eqv BMPHeader_width 18
.eqv BMPHeader_height 22


.eqv system_OpenFile	1024
.eqv system_ReadFile	63
.eqv system_WriteFile	64
.eqv system_CloseFile	57

	.data
imgInfo: .space	24	# image descriptor

	.align 2		# word boundary alignment
dummy:		.space 2
bmpHeader:	.space	BMPHeader_Size

	.align 2
imgData: 	.space	MAX_IMG_SIZE

ifname:	.asciz "test_1.bmp"
ofname: .asciz "result.bmp"

#--------------- Params ---------------
.eqv Rsel		221
.eqv Gsel		153
.eqv Bsel		121
.eqv dist		344
#--------------------------------------
	.text
main:
	# filling image descriptor
	la a0, imgInfo 
	la t0, ifname
	sw t0, ImgInfo_fname(a0)
	la t0, bmpHeader
	sw t0, ImgInfo_hdrdat(a0)
	la t0, imgData
	sw t0, ImgInfo_imdat(a0)
	jal	read_bmp
	bnez a0, main_failure
	
	la a0, imgInfo
	jal replace_to_sepia

	la a0, imgInfo
	la t0, ofname
	sw t0, ImgInfo_fname(a0)
	jal save_bmp

main_failure:
	li a7, 10
	ecall

# read_bmp: 
#	reads the content of a bmp file into memory
# arguments:
#	a0 - address of image descriptor structure
#		input filename pointer, header and image buffers should be set
# return value: 
#	a0 - 0 if successful, error code in other cases
read_bmp:
	mv t0, a0	# preserve imgInfo structure pointer
	
#open file
	li a7, system_OpenFile
	lw a0, ImgInfo_fname(t0)	#file name 
	li a1, 0			#flags: 0-read file
	ecall
	
	blt a0, zero, rb_error
	mv t1, a0			# save file handle for the future
	
#read header
	li a7, system_ReadFile
	lw a1, ImgInfo_hdrdat(t0)
	li a2, BMPHeader_Size
	ecall
	
#extract image information from header
	lw a0, BMPHeader_width(a1)
	sw a0, ImgInfo_width(t0)
	
#compute line size in bytes - bmp line has to be multiple of 4
	add a2, a0, a0
	add a0, a2, a0	# pixelbytes = width * 3 
	addi a0, a0, 3
	srai a0, a0, 2
	slli a0, a0, 2	# linebytes = ((pixelbytes + 3) / 4 ) * 4
	sw a0, ImgInfo_lbytes(t0)
	
	lw a0, BMPHeader_height(a1)
	sw a0, ImgInfo_height(t0)

#read image data
	li a7, system_ReadFile
	mv a0, t1
	lw a1, ImgInfo_imdat(t0)
	li a2, MAX_IMG_SIZE
	ecall

#close file
	li a7, system_CloseFile
	mv a0, t1
    ecall
	
	mv a0, zero
	jr ra
	
rb_error:
	li a0, 1	# error opening file	
	jr ra
	
# save_bmp - saves bmp file stored in memory to a file
# arguments:
#	a0 - address of ImgInfo structure containing description of the image`
# return value: 
#	a0 - zero if successful, error code in other cases

save_bmp:
	mv t0, a0	# preserve imgInfo structure pointer
	
#open file
	li a7, system_OpenFile
	lw a0, ImgInfo_fname(t0)	#file name 
	li a1, 1			#flags: 1-write file
	ecall
	
	blt a0, zero, wb_error
	mv t1, a0			# save file handle for the future
	
#write header
	li a7, system_WriteFile
	lw a1, ImgInfo_hdrdat(t0)
	li a2, BMPHeader_Size
	ecall
	
#write image data
	li a7, system_WriteFile
	mv a0, t1
	lw a2, ImgInfo_lbytes(t0)
	lw a1, ImgInfo_height(t0)
	mul a2, a2, a1		# compute image size (linebytes * height)
	lw a1, ImgInfo_imdat(t0)
	ecall

#close file
	li a7, system_CloseFile
	mv a0, t1
	ecall
	
	mv a0, zero
	jr ra
	
wb_error:
	li a0, 2 # error writing file
	jr ra

# ============================================================================
# replace_to_sepia - converts appropiate pixels of BMP image to sepia tones
#arguments:
#	a0 - address of ImgInfo image descriptor
#return value:
#	none

replace_to_sepia:			
	lw a2, ImgInfo_height(a0)
	mv a4, a0	#preserve imgInfo for further use
	addi a2, a2, -1		
	
get_line:
	lw a1, ImgInfo_width(a0)
	addi a1, a1, -1
	
get_pixel:
	lw t1, ImgInfo_lbytes(a0)
	mul t1, t1, a2  # t1 = y * linebytes
	add a3, a1, a1
	add a3, a3, a1 	# a3 = x * 3
	add a3, a3, t1  # a3 is offset of the pixel

	lw t1, ImgInfo_imdat(a0) # address of image data
	add a3, a3, t1 	# a3 is address of the pixel
	
	lbu t0, (a3)	#inputBlue
	lbu t1, 1(a3)	#inputGreen
	lbu t2, 2(a3)	#inputRed

calculate_distance:
	li t6, Rsel
	sub a5, t2, t6	#R - Rsel
	mul a5, a5, a5	#(R - Rsel)^2
	li t6, Gsel
	sub a6, t1, t6	#G - Gsel
	mul a6, a6, a6	#(G - Gsel)^2
	sub a5, a5, a6	#(R - Rsel)^2 - (G - Gsel)^2
	li t6, Bsel
	sub a6, t0, t6	#B - Bsel
	mul a6, a6, a6	#(B - Bsel)^2
	sub a5, a5, a6	#(R - Rsel)^2 - (G - Gsel)^2 - (B - Bsel)^2
	li t6, dist
	mul t6, t6, t6	#distance^2 to avoid sqrt
	blt t6, a5, next_iteration

calculate_red:
#t3 - outputRed = [(inputRed * .393) + (inputGreen *.769) + (inputBlue * .189)] *1024 /1024
#multiply by 1024 to avoid using floating point unit and increase division efficiency
	li t6, 402 
	mul t3, t6, t2
	li t6, 787
	mul t6, t6, t1
	add t3, t3, t6
	li t6, 194
	mul t6, t6, t0
	add t3, t3, t6
	srli t3, t3, 10	#/1024
	li t6, 255
	ble t3, t6, calculate_green
	mv t3, t6
	
calculate_green:
#t4 - outputGreen = [(inputRed * .349) + (inputGreen *.686) + (inputBlue * .168)] * 1024 /1024
	li t6, 403
	mul t4, t6, t2
	li t6, 702
	mul t6, t6, t1
	add t4, t4, t6
	li t6, 172
	mul t6, t6, t0
	add t4, t4, t6
	srli t4, t4, 10
	li t6, 255
	ble t4, t6, calculate_blue
	mv t4, t6
	
calculate_blue:
#t5 - outputBlue = [(inputRed * .272) + (inputGreen *.534) + (inputBlue * .131)] * 1024 /1024
	li t6, 279
	mul t5, t6, t2
	li t6, 547
	mul t6, t6, t1
	add t5, t5, t6
	li t6, 134
	mul t6, t6, t0
	add t5, t5, t6
	srli t5, t5, 10
	li t6, 255
	ble t5, t6, set_color
	mv t5, t6
	
set_color:
	mv a0, a4
	lw t1, ImgInfo_lbytes(a0)
	mul t1, t1, a2  # t1 = y * linebytes
	add t0, a1, a1
	add t0, t0, a1 	# t0 = x * 3
	add t0, t0, t1  # t0 is offset of the pixel

	lw t1, ImgInfo_imdat(a0) # address of image data
	add t0, t0, t1 	# t0 is address of the pixel

	sb   t3,(t0)		#store outputBlue
	sb   t4, 1(t0)		#store outputGreen
	sb   t5, 2(t0)		#store outputRed
	
next_iteration:
	addi a1, a1, -1
	bge a1, zero, get_pixel
	
	addi a2, a2, -1
	bge a2, zero, get_line
	
	jr ra
