## Synchronization of processes using semaphores

You should write a program in the C language in the Linux environment realising
solving the problem related to the organisation of N communication buffers, between which there are additional ties are imposed.

We have 4 buffers of length N. These are: dough buffer, meat buffer, cheese buffer, cabbage buffer. We have 4 types of producers who produce: dough, meat, cheese and cabbage, then place the produced product into the corresponding buffer. Consumers make dumplings of 3 types: with meat, with cheese, with cabbage. The condition for making a dumpling is that one portion of dough and one portion of filling are available in the buffers at any one time. The number of processes/threads of producers and consumers should be a programme parameter.