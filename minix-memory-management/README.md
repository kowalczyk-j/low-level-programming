## Minix memory management

By default in the Minix system, the algorithm for selecting a free block from a list of
free blocks list, used to implement system functions FORK and
EXEC, is the first fit algorithm, i.e. the first block of
of memory of sufficient size from the list of free blocks is selected.

The aim of the exercise is to change the default memory allocation algorithm in the
Minix system. You should be able to choose the block selection algorithm from a list of
free blocks list between the standard first fit and the so-called worst fit algorithm, i.e. one in which the first block of sufficient size is selected from the free block list.
fit algorithm, i.e. one in which a memory block is selected from a list of free
blocks with the largest size.

Implement the worst fit algorithm in the system and then
demonstrate and interpret the differences in the performance of the respective algorithms.