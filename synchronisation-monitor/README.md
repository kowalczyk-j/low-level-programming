## Synchronization of processes using monitors

You must write a C++ program in a Linux executing environment. The 'communication buffer' type should be realised with a monitor. During implementation, synchronisation must be ensured.

We have 4 buffers of length N. These are: dough buffer, meat buffer, cheese buffer, cabbage buffer. We have 4 types of producers who produce: dough, meat, cheese and cabbage, then place the produced product into the corresponding buffer. Consumers make dumplings of 3 types: with meat, with cheese, with cabbage. The condition for making a dumpling is that one portion of dough and one portion of filling are available in the buffers at any one time. The number of processes/threads of producers and consumers should be a programme parameter.