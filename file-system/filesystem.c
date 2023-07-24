#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "filesystem.h"


int createVirtualDisk(int diskSize, char* diskName) {
    SuperBlock header;
    Inode inode;
    int s = diskSize * (1024 / BLOCK_SIZE);
    char* blockTable;
    int i;

    // Otwarcie pliku dysku w trybie binarnym do zapisu
    FILE* disk = fopen(diskName, "wb");

    // Zapisanie nagłówka dysku
    header.blockSize = BLOCK_SIZE;
    header.totalSize = diskSize * BLOCK_SIZE;
    header.filesAmount = 0;
    header.firstAddress = INODE_BLOCKS + 2;
    header.spaceLeft = header.totalSize - header.firstAddress * header.blockSize;
    fwrite(&header, sizeof(header), 1, disk);
    
    // Przesunięcie wskaźnika pliku na pozycję BLOCK_SIZE
    fseek(disk, BLOCK_SIZE, SEEK_SET);

    // Alokacja pamięci dla tablicy bloków
    blockTable = malloc(s);
    
    // Ustawienie początkowych wartości tablicy bloków
    for (i = 0; i < s; i++) {
        blockTable[i] = i < header.firstAddress ? 1 : 0;
    }
    // Zapisanie tablicy bloków
    fwrite(blockTable, sizeof(blockTable[0]), s, disk);
    fseek(disk, BLOCK_SIZE * 2, SEEK_SET);

    // Ustawienie początkowych wartości inodów
    inode.size = 0;
    inode.beginning = 0;
    memset(inode.name, '\0', sizeof(inode.name) / sizeof(char));

    // Zapisanie inodów
    for (i = 0; i < 2 * BLOCK_SIZE / sizeof(inode); i++) {
        fwrite(&inode, sizeof(inode), 1, disk);
    }
    printf("Virtual disk %s created.\n", diskName);

    // Zamykanie pliku dysku
    fclose(disk);

    // Zwolnienie pamięci
    free(blockTable);
    return 0;
}

int copyFileToVirtualDisk(char* diskName, char* fileName) {
    FILE* disk;
    FILE* file;
    SuperBlock diskHeader;
    Inode node;
    long offset;
    char* blockTable;
    char* content;
    int nodeNum = 0;
    int fileBeginning = -1;
    int i, j, k, fileBlockAmount, blockTableSize;

    if (strlen(fileName) > FILENAME_SIZE) {
        printf("File name is too long.\n");
        return 1;
    }
    // Otwarcie pliku dysku w trybie binarnym do odczytu i zapisu
    disk = fopen(diskName, "r+b");
    if (disk == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    // Otwarcie pliku do skopiowania w trybie binarnym do odczytu
    file = fopen(fileName, "rb");
    if (file == NULL) {
        printf("File to copy doesn't exist.\n");
        return 1;
    }
    fread(&diskHeader, sizeof(SuperBlock), 1, disk);
    fseek(file, 0, SEEK_END);
    offset = ftell(file);
    if (diskHeader.spaceLeft < offset) {
        printf("Not enough space on virtual disk.\n");
        return 1;
    }
    // Alokacja pamięci dla zawartości pliku
    fileBlockAmount = offset / diskHeader.blockSize;
    if (offset % diskHeader.blockSize != 0) {
        fileBlockAmount++;
    }
    fseek(file, 0, SEEK_SET);
    blockTableSize = diskHeader.totalSize / diskHeader.blockSize;
    blockTable = malloc(blockTableSize * sizeof(char));


    fseek(disk, diskHeader.blockSize, SEEK_SET);
    fread(blockTable, sizeof(char), blockTableSize, disk);
    fseek(disk, diskHeader.blockSize * 2, SEEK_SET);

    // Sprawdzenie czy plik o takiej nazwie już istnieje
    for (i = 0, k = 0; i < diskHeader.filesAmount; k++) {
        if (fread(&node, sizeof(Inode), 1, disk)) {
            if (node.isUsed) {
                i++;
                if (k == nodeNum) {
                    nodeNum++;
                }
                if (strcmp(fileName, node.name) == 0) {
                    printf("File with the same name already exists.\n");
                    return 0;
                }
            }
        }
    }
    // Przeszukanie tablicy bloków w poszukiwaniu wolnych miejsc
    for (i = diskHeader.firstAddress; i < blockTableSize; i++) {
        for (j = 0; j < fileBlockAmount; j++) {
            if (blockTable[i + j] == 1 || i + j >= blockTableSize)
                break;
        }
        if (j == fileBlockAmount) {
            fileBeginning = i;
            break;
        }
    }
    if (fileBeginning == -1) {
        printf("Not enough space on virtual disk.\n");
        return 1;
    }
    for (i = 0; i < fileBlockAmount; i++) {
        blockTable[fileBeginning + i] = 1;
    }
    // Zapisanie tablicy bloków
    node.blocksAmount = fileBlockAmount;
    node.beginning = fileBeginning;
    node.isUsed = 1;
    node.size = offset;
    strncpy(node.name, fileName, sizeof(node.name) / sizeof(char));
    diskHeader.spaceLeft -= fileBlockAmount * diskHeader.blockSize;
    diskHeader.filesAmount += 1;
    fseek(disk, fileBeginning * diskHeader.blockSize, SEEK_SET);
    fseek(file, 0, SEEK_SET);
    content = malloc(offset);
   
    // Zapisanie zawartości pliku
    fread(content, sizeof(char), offset / sizeof(char), file);
    fwrite(content, sizeof(char), offset / sizeof(char), disk);
    fseek(disk, 0, SEEK_SET);
    fwrite(&diskHeader, sizeof(SuperBlock), 1, disk);
    fseek(disk, diskHeader.blockSize, SEEK_SET);  
    fwrite(blockTable, sizeof(char), blockTableSize, disk);
    fseek(disk, diskHeader.blockSize * 2 + nodeNum * sizeof(Inode), SEEK_SET);
    fwrite(&node, sizeof(Inode), 1, disk);

    printf("File %s copied to virtual disk %s.\n", fileName, diskName);

    // Zamykanie plików
    fclose(file);
    fclose(disk);
    free(blockTable);
    free(content);
    return 0;
}

int copyFileFromVirtualDisk(char* diskName, char* fileName){
    FILE* disk;
    FILE* file;
    SuperBlock diskHeader;
    Inode node;
    char* contents;
    char found = 0;
    int i;

    disk = fopen(diskName, "rb");
    if (disk == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    
    fread(&diskHeader, sizeof(SuperBlock), 1, disk);
    fseek(disk, diskHeader.blockSize * 2, SEEK_SET);
    
    // Sprawdzenie czy plik istnieje na dysku
    i = 0;
    while (i < diskHeader.filesAmount) {
        fread(&node, sizeof(Inode), 1, disk);
            if (node.isUsed == 1) {
                i++;
                if (strcmp(fileName, node.name) == 0) {
                    found = 1;
                    break;
                }
            }
    }
    if (found == 0) {
        printf("File not found.\n");
        return 1;
    }

    contents = malloc(node.size);
    fseek(disk, node.beginning * diskHeader.blockSize, SEEK_SET);
    fread(contents, sizeof(char), node.size, disk);
    file = fopen(fileName, "wb");
    fwrite(contents, sizeof(char), node.size, file);
    printf("File %s copied from virtual disk %s.\n", fileName, diskName);
    fclose(file);
    fclose(disk);
    free(contents);
    return 0;
}


int displayCatalog(char* diskName) {
    SuperBlock diskHeader;
    Inode node;
    int i;

    FILE* disk = fopen(diskName, "rb");
    if (disk == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    printf("Virtual disk %s catalog:\n", diskName);
    printf("Filename\tSize (kB)\tAmount of blocks\n");
    fread(&diskHeader, sizeof(SuperBlock), 1, disk);
    fseek(disk, diskHeader.blockSize * 2, SEEK_SET);
    i = 0;
    while (i < diskHeader.filesAmount) {
        fread(&node, sizeof(Inode), 1, disk);
            if (node.isUsed) {
                printf("%s\t\t%d\t\t\t%d\n", node.name, node.size, node.blocksAmount);
                i++;
            }
    }
    fclose(disk);
    return 0;
}

int deleteFileFromVirtualDisk(char* diskName, char* fileName){
    SuperBlock diskHeader;
    Inode node;
    char* blockTable;
    char found = 0;
    int i, j, k, nodeNum, blockTableSize;

    FILE* disk = fopen(diskName, "r+b");
    if (disk == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    fread(&diskHeader, sizeof(SuperBlock), 1, disk);
    if (diskHeader.filesAmount == 0) {
        printf("Virtual disk is empty.\n");
        fclose(disk);
        return 1;
    }
    blockTableSize = diskHeader.totalSize / diskHeader.blockSize;
    blockTable = malloc(blockTableSize * sizeof(char));
    fread(blockTable, sizeof(char), blockTableSize, disk);
    fseek(disk, diskHeader.blockSize * 2, SEEK_SET);
    i = 0;
    while (i < diskHeader.filesAmount) {
        fread(&node, sizeof(Inode), 1, disk);
        if (node.isUsed) {
            i++;
            if (strcmp(fileName, node.name) == 0) {
                found = 1;
                nodeNum = i - 1;
                break;
            }
        }
    }
    if (found == 0) {
        printf("Error no such file in directory.\n");
        fclose(disk);
        return 1;
    }
    for (i = node.beginning; i < node.beginning + node.blocksAmount; i++) {
        blockTable[i] = 0;
    }
    diskHeader.spaceLeft += node.blocksAmount * diskHeader.blockSize;
    diskHeader.filesAmount -= 1;
    node.isUsed = 0;
    fseek(disk, 0, SEEK_SET);
    fwrite(&diskHeader, sizeof(SuperBlock), 1, disk);
    fseek(disk, diskHeader.blockSize, SEEK_SET);
    fwrite(blockTable, sizeof(char), blockTableSize, disk);
    fseek(disk, diskHeader.blockSize * 2 + nodeNum * sizeof(Inode), SEEK_SET);
    fwrite(&node, sizeof(Inode), 1, disk);
    printf("File %s deleted from virtual disk %s.\n", fileName, diskName);
    fclose(disk);
    free(blockTable);
    return 0;
}

int deleteVirtualDisk(char* diskName) {
    if(fopen(diskName, "rb") == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    printf("Virtual disk %s deleted.\n", diskName);
    return remove(diskName);
}

int renameVirtualDisk(char* diskName, char* newDiskName) {
    if(fopen(diskName, "rb") == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    printf("Virtual disk %s renamed to %s.\n", diskName, newDiskName);
    return rename(diskName, newDiskName);
}

int showMemoryMap(char* diskName) {
    FILE* disk = fopen(diskName, "rb");
    if (disk == NULL) {
        printf("Virtual disk doesn't exist.\n");
        return 1;
    }
    SuperBlock diskHeader;
    fread(&diskHeader, sizeof(SuperBlock), 1, disk);
    int blockTableSize = diskHeader.totalSize / diskHeader.blockSize;
    char* blockTable = malloc(blockTableSize * sizeof(char));
    fseek(disk, diskHeader.blockSize, SEEK_SET);
    fread(blockTable, sizeof(char), blockTableSize, disk);

    printf("Virtual disk map:\n");
    printf("Address\t\tSize (B)\tState (Free/Occupied)\n");
    for (int i = 0; i < blockTableSize; i++) {
        if (i < diskHeader.firstAddress) {
            printf("%d\t\t%d\t\tOccupied\n", i, diskHeader.blockSize);
        } else {
            printf("%d\t\t%d\t\t", i, diskHeader.blockSize);
            if (blockTable[i]) {
                printf("Occupied\n");
            } else {
                printf("Free\n");
            }
        }
    }
    fclose(disk);
    free(blockTable);
    return 0;
}

int main(int argc, char* argv[]) {
    char* command = argv[1];
    if ( argc < 2 || (argc == 2 && strcmp(command, "h") !=0) || 
    (argc == 3 && strcmp(command, "ls") != 0 && strcmp(command, "delete") != 0 && strcmp(command, "info")!=0) ||
    (argc == 4 && strcmp(command, "create") != 0 && strcmp(command, "send") != 0 &&
    strcmp(command, "get") != 0 && strcmp(command, "rm") != 0 && strcmp(command, "mv") != 0)) {
        printf("Invalid arguments, please enter h for help.\n");
        return 1;
    }
    if (strcmp(command, "h") == 0) {
        printf("List of options (h):\n");
        printf("create\t<diskname>\t<size(kB)>\t- Create virtual disk\n");
        printf("send\t<diskname>\t<filename>\t- Copy file to virtual disk\n");
        printf("get\t<diskname>\t<filename>\t- Copy file from virtual disk\n");
        printf("ls\t<diskname>\t\t\t- Display list of files in virtual disk\n");
        printf("rm\t<diskname>\t<filename>\t- Delete file from virtual disk\n");
        printf("delete\t<diskname>\t\t\t- Delete virtual disk\n");
        printf("info\t<diskname>\t\t\t- Display virtual disk's memory map\n");
        printf("mv\t<diskname>\t<NewName>\t- Rename virtual disk\n");
        return 0;
    }
    switch (command[0]) {
        case 'c': return createVirtualDisk(atoi(argv[3]), argv[2]);
        case 's': return copyFileToVirtualDisk(argv[2], argv[3]);
        case 'g': return copyFileFromVirtualDisk(argv[2], argv[3]);
        case 'l': return displayCatalog(argv[2]);
        case 'r': return deleteFileFromVirtualDisk(argv[2], argv[3]);
        case 'd': return deleteVirtualDisk(argv[2]);
        case 'i': return showMemoryMap(argv[2]);
        case 'm': return renameVirtualDisk(argv[2], argv[3]);
    }
    return 0;
}