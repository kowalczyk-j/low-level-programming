#include <semaphore.h>
#include <string>
#include <queue>
#include "monitor.h"

#define BUFFER_SIZE 10

class Buffer : public Monitor
{
    std::string type;
    Condition full, empty;
    std::queue<bool> buffer;

public:
    Buffer(std::string type)// Konstruktor, w którym przypisujemy nazwę składnika do zmiennej "type"
    {
        this -> type = type;
    }
    void produce()          // Funkcja producenta, która umieszcza element w buforze
    {
        enter();            // Wejście do sekcji krytycznej
        if (buffer.size() == BUFFER_SIZE)
            wait(full);     // Jeśli bufor jest pełny, to wstrzymujemy wątek
        buffer.push(1);     // Dodajemy element do bufora
        if (buffer.size() == 1)
            signal(empty);  // Jeśli bufor jest niepusty, to sygnalizujemy wątkowi konsumenta, że może usunąć element z bufora
        leave();            // Opuszczamy sekcję krytyczną
    }
  
    void consume()          // Funkcja konsumenta, która usuwa element z bufora
    {
        enter();
        if (buffer.empty())
            wait(empty);    // Jeśli bufor jest pusty, to wstrzymujemy wątek
        buffer.pop();       // Usuwamy element z bufora
        if (buffer.size() == BUFFER_SIZE - 1)
            signal(full);   // Jeśli bufor jest niepełny, to sygnalizujemy wątkowi producnenta, że może dodać element do bufora
        leave();
    }
    std::string get_type() { return type; }
    int get_size() { return buffer.size(); }
};