#pragma once

#define BLOCK_SIZE 1024
#define INODE_BLOCKS 2
#define FILENAME_SIZE 16

typedef struct SuperBlock {
    int blockSize;
    int totalSize;
    int spaceLeft;
    int filesAmount;
    int firstAddress;
} SuperBlock;

typedef struct Inode {
    int isUsed;
    int size;
    int beginning;
    int blocksAmount;
    char name[FILENAME_SIZE];
} Inode;