#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <semaphore.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>

#define BUFFER_SIZE 10
#define SLOW_MODE 1
#define DEBUG_MODE 1

struct Buffer {
    char type[10];
    sem_t sem_empty;
    sem_t sem_full;
    pthread_mutex_t mutex;
    int count;
    int ingredient[BUFFER_SIZE];
};

struct Buffer dough_buffer, meat_buffer, cheese_buffer, cabbage_buffer;

void init_buffer(struct Buffer* buffer, char* buffer_type) {
    strcpy(buffer->type, buffer_type);
    pthread_mutex_init(&buffer->mutex, NULL);
    sem_init(&buffer->sem_empty, 0, BUFFER_SIZE);
    sem_init(&buffer->sem_full, 0, 0);
    buffer->count = 0;
    for (int i = 0; i < BUFFER_SIZE; i++) {
        buffer->ingredient[i] = 0;
    }
}

void print_buffer(struct Buffer* buffer) {
    printf("Bufor %s: ", buffer->type);
    for (int i = 0; i < BUFFER_SIZE; i++) {
        printf("%d ", buffer->ingredient[i]);
    }
    printf("\n");
}

void* produce_ingredients(void* buffer) {
    struct Buffer* buf = (struct Buffer*) buffer;
    while(1) {
        if(SLOW_MODE) sleep(2);
        sem_wait(&buf->sem_empty);
        pthread_mutex_lock(&buf->mutex);
        buf->ingredient[buf->count++] = 1;
        printf("Wyprodukowano: %s Pozycja bufora: %d\n", buf->type, buf->count);
        if(DEBUG_MODE) print_buffer(buf);
        pthread_mutex_unlock(&buf->mutex);
        sem_post(&buf->sem_full);
    }
}

void* consume_for_dumplings(void* buffer) {
    struct Buffer* buf = (struct Buffer*) buffer;
    while (1) {
        if(SLOW_MODE) sleep(2);
        sem_wait(&buf->sem_full);
        sem_wait(&dough_buffer.sem_full);
        pthread_mutex_lock(&dough_buffer.mutex);
        pthread_mutex_lock(&buf->mutex);
        dough_buffer.ingredient[--dough_buffer.count] = 0;
        buf->ingredient[--buf->count] = 0;
        printf("Konsumpcja: pierogi ze składnikiem %s\n", buf->type);
        if (DEBUG_MODE){
            print_buffer(buf);
            print_buffer(&dough_buffer);
        }
        pthread_mutex_unlock(&dough_buffer.mutex);
        pthread_mutex_unlock(&buf->mutex);
        sem_post(&buf->sem_empty);
        sem_post(&dough_buffer.sem_empty);
    }
}

void destroy_buffer(struct Buffer* buffer) {
    sem_destroy(&buffer->sem_empty);
    sem_destroy(&buffer->sem_full);
    pthread_mutex_destroy(&buffer->mutex);
}

int main(int argc, char* argv[]) {
    // p - liczba wątków producentów, c - liczba wątków konstumentów
    int p_dough, p_meat, p_cheese, p_cabbage, c_meat, c_cheese, c_cabbage; 
    if (argc != 8) {
        printf("Błędne argumenty. Podaj nazwę pliku oraz 7 argumentów\n");
        printf("Liczba wątków kolejno 4 producentów (ciasto, mięso, ser, kapusta) oraz 3 konsumentów (bez ciasta).\n");
        return -1;
    }
    //Wczytanie argumentów - kolejnych liczb wątków
    p_dough = atoi(argv[1]);
    p_meat = atoi(argv[2]);
    p_cheese = atoi(argv[3]);
    p_cabbage = atoi(argv[4]);
    c_meat = atoi(argv[5]);
    c_cheese = atoi(argv[6]);
    c_cabbage = atoi(argv[7]);

    //Inicjalizacja semaforów i buforów
    init_buffer(&dough_buffer, "ciasto");
    init_buffer(&meat_buffer, "mięso");
    init_buffer(&cheese_buffer, "ser");
    init_buffer(&cabbage_buffer, "kapusta");

    //Utworzenie tablic wątków
    int num_producers= p_dough + p_meat + p_cheese + p_cabbage;
    int num_consumers = c_meat + c_cheese + c_cabbage;
    pthread_t producer_threads[num_producers], consumer_threads[num_consumers];

    //Inicjalizacja wątków
    for (int i = 0; i < p_dough; i++) {
        pthread_create(&producer_threads[i], NULL, produce_ingredients, &dough_buffer);
    }
    for (int i = 0; i < p_meat; i++) {
        pthread_create(&producer_threads[i+p_dough], NULL, produce_ingredients, &meat_buffer);
    }
    for (int i = 0; i < p_cheese; i++) {
        pthread_create(&producer_threads[i+p_dough+p_meat], NULL, produce_ingredients, &cheese_buffer);
    }
    for (int i = 0; i < p_cabbage; i++) {
        pthread_create(&producer_threads[i+p_dough+p_meat+p_cheese], NULL, produce_ingredients, &cabbage_buffer);
    }
    for (int i = 0; i < c_meat; i++) {
        pthread_create(&consumer_threads[i], NULL, consume_for_dumplings, &meat_buffer);
    }
    for (int i = 0; i < c_cheese; i++) {
        pthread_create(&consumer_threads[i+c_meat], NULL, consume_for_dumplings, &cheese_buffer);
    }
    for (int i = 0; i < c_cabbage; i++) {
        pthread_create(&consumer_threads[i+c_meat+c_cheese], NULL, consume_for_dumplings, &cabbage_buffer);
    }

    //Działanie wątków
    for (int i = 0; i < num_producers; i++) {
        pthread_join(producer_threads[i], NULL);
    }
    for (int i = 0; i < num_consumers; i++) {
        pthread_join(consumer_threads[i], NULL);
    }

    //Zniszczenie semaforów
    destroy_buffer(&dough_buffer);
    destroy_buffer(&meat_buffer);
    destroy_buffer(&cheese_buffer);
    destroy_buffer(&cabbage_buffer);
    return 0;
}