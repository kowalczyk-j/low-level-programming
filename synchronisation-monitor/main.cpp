#include <iostream>
#include <random>
#include <vector>
#include <algorithm>
#include "buffer.h"

#define SLOW_MODE 0

// Tworzenie obiektów klasy Buffer odpowiedzialnych za odpowiedni składnik
Buffer dough_buffer("ciasto"), meat_buffer("mięso"), cheese_buffer("ser"), cabbage_buffer("kapusta");


void* produce_ingredients(void* buffer) {
    struct Buffer* buf = (struct Buffer*) buffer;
    while(1) {
        if(SLOW_MODE) sleep(2);
        buf->produce();
        if(buf->get_size()>BUFFER_SIZE)
            printf("PRZEPEŁNIENIE BUFORA przez producenta %s rozmiar: %d \n", buf->get_type().c_str(),buf->get_size());
    }
}

void* consume_for_dumplings(void* buffer) {
    struct Buffer* buf = (struct Buffer*) buffer;
    while (1) {
        if(SLOW_MODE) sleep(2);
        buf->consume();
        dough_buffer.consume();
        if(buf->get_size()>BUFFER_SIZE)
            printf("PRZEPEŁNIENIE BUFORA przez konsumenta %s rozmiar: %d \n", buf->get_type().c_str(),buf->get_size());
        if(dough_buffer.get_size()>BUFFER_SIZE) 
            printf("PRZEPEŁNIENIE BUFORA przez konsumenta ciasta rozmiar: %d \n", dough_buffer.get_size());
        printf("Konsumpcja: pierogi ze składnikiem %s\n", buf->get_type().c_str());
    }
}

int main(int argc, char* argv[]) {
    // p - liczba wątków producentów, c - liczba wątków konstumentów
    int p_dough, p_meat, p_cheese, p_cabbage, c_meat, c_cheese, c_cabbage; 
    if (argc != 8) {
        std::cout<<"Błędne argumenty. Podaj nazwę pliku oraz 7 argumentów\n";
        std::cout<<"Liczba wątków kolejno 4 producentów (ciasto, mięso, ser, kapusta) oraz 3 konsumentów (bez ciasta).\n";
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

    //Utworzenie tablic wątków
    int num_producers= p_dough + p_meat + p_cheese + p_cabbage;
    int num_consumers = c_meat + c_cheese + c_cabbage;
    pthread_t producer_threads[num_producers], consumer_threads[num_consumers];

    //Inicjalizacja wątków producentów
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
    //Inicjalizacja wątków konsumentów
    for (int i = 0; i < c_meat; i++) {
        pthread_create(&consumer_threads[i], NULL, consume_for_dumplings, &meat_buffer);
    }
    for (int i = 0; i < c_cheese; i++) {
        pthread_create(&consumer_threads[i+c_meat], NULL, consume_for_dumplings, &cheese_buffer);
    }
    for (int i = 0; i < c_cabbage; i++) {
        pthread_create(&consumer_threads[i+c_meat+c_cheese], NULL, consume_for_dumplings, &cabbage_buffer);
    }

    //Randomizacja startu wątków
    std::vector<int> p_indices(num_producers);
    std::vector<int> c_indices(num_consumers);
    std::random_device rd;
    std::mt19937 g(rd());
    std::shuffle(p_indices.begin(), p_indices.end(), g);
    std::shuffle(c_indices.begin(), c_indices.end(), g);

    //Działanie wątków
    for (auto i : p_indices) {
        pthread_join(producer_threads[i], NULL);
    }
    for (auto i : c_indices) {
        pthread_join(consumer_threads[i], NULL);
    }

    return 0;
}