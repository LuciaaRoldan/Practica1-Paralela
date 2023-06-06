
#PRÁCTICA 1. Parte obligatoria.
#LUCÍA ROLDÁN RODRÍGUEZ.

from multiprocessing import Process,Manager
from multiprocessing import  Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import  Array
from time import sleep
import random

NPROD = 4 #número de productores.
N = 3 # número de veces que produce cada productor.

#La función new_data genera un valor mayor que el último producido, en un rango de 10 unidades.
def new_data(ultimo_valor):
    a = random.randint(1,10)
    return (ultimo_valor + a)

# La función delay tiene como objetivo simular un tiempo de producción y consumición.
def delay(factor = 3):
    sleep(random.random()/factor)

def producer(valores,non_empty,empty,mutex):
    ultimo_valor = 0 # En esta variable se almacenará el último valor producido por el productor
    i = int(current_process().name.split('_')[1]) # índice del productor
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        empty.acquire() # Se va a actualizar el elemento almacenado.
        # Por tanto se comprueba si la posición está libre.
        mutex.acquire()#para asegurarnos de que varios procesos no editan a la vez variables compartidas
        ultimo_valor = new_data(ultimo_valor) # Se genera el nuevo valor.
        valores[i] = ultimo_valor # Se actualiza en la posición respectiva del productor el nuevo valor
        print (f"producer {current_process().name} ha almacenado {ultimo_valor}")
        mutex.release()
        non_empty.release() #se aumenta en uno la capacidad del semáforo encargado de regular
        # la existencia de valores antes de consumir.
    # Por último se repite el proceso añadiendo un -1 como símbolo de finalización de la produción.
    empty.acquire()
    valores[i] = -1
    print (f"producer {current_process().name} ha terminado de producir")
    non_empty.release()


#La función minimo devuelve el mínimo valor distinto de -1  en una lista
#así como el índice de la posición en que se encuentra.
def minimo(storage,mutex):
    mutex.acquire()
    indice = 0
    valor = storage[0]
    #Se asegura de que no se haya inicializado en -1
    while valor == -1 :
        indice +=1
        valor = storage[indice]
    # Se comprueba si existe un valor menor diferente de -1 a lo largo de
    # la lista en cuyo caso se actualiza el índice y el valor.
    for k in range(1,len(storage)):
        if storage[k] < valor and storage[k] != -1 :
            valor = storage[k]
            indice = k
    mutex.release()
    return(indice,valor)

# la función stiLl_producing sirve para comprobar si algún productor sigue produciendo
# para ello comprueba que la lista pasada por parámetro no esté confomrada exclusivamente
# por -1.
def still_producing(storage,mutex):
    mutex.acquire()
    for k in range(len(storage)):
        if storage[k] != -1:
            mutex.release()
            return(True)
    mutex.release()
    return(False)
    


def consumer(valores, sol,non_empty_list,empty_list,mutex):
    # Se espera hasta que todas la posiciones de los productores hayan sido cubiertas.
    for i in range(NPROD):
        non_empty_list[i].acquire()
    # Mientras haya algún productor que siga produciendo se entrará en el bucle
    while still_producing(valores,mutex):
        indice, valor =  minimo(valores,mutex)#indice del productor con el mínimo elemento y valor del elemento mínimo
        sol.append(valor) # añadimos el valor a la solución
        valores[indice] = -2 # se actualiza la posición como vacía en dicho productor.
        print (f"consumido {valor} del productor {indice}")
        # Se aumenta en uno la capacidad del semáforo (del proceso del cual se ha consumido)
        # que se encarga de comprobrar que esté libre la posición de almacenaje antes de producir.
        empty_list[indice].release()
        delay()
        # se reduce en uno la capacidad del semáforo encargado de comprobrar
        # que existe un valor almacenado por dicho productor.
        non_empty_list[indice].acquire()


def main():
     # En el array valores_consumidores se almacenará el último valor
     # almacenado por cada productor
     valores_consumidores = Array('i', NPROD)
     # Se inicializan todos los valores como vacíos con un -2
     for i in range(len(valores_consumidores)):
         valores_consumidores [i] = -2

     # Solución es la lista donde se irán almacenando de forma ordenada
     # los valores producidos.
     manager = Manager()
     solucion= manager.list()
     
     mutex = Lock()  # Regula que solo haya un proceso editando la lista de productos al mismo tiempo.

     # Se crea una lista de semáforos que regularán que cuando vaya a consumir el
     # consumidor exista un valor producido por todos los productores que no
     # hayan terminado de producir.
     non_empty_list = [Semaphore(0) for i in range(NPROD)]

     # Se crea una lista de semáforos encargados de regular que no se produzca
     # si no hay hueco puesto que supondría una pérdida de información.
     empty_list = [Lock() for i in range(NPROD)]
     # Se crean NPROD procesos, cada uno con la lista valores_consumidores
     # y sus semáforos correspondientes.
     prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(valores_consumidores,non_empty_list[i], empty_list[i],mutex))
                for i in range(NPROD) ]
     # Se crea un consumidor que recibe por parámetros, la lista de valores producidos, la lista solución
     # y ambas listas de semáforos.
     consumidor = Process(target=consumer,args=(valores_consumidores,solucion,non_empty_list, empty_list,mutex))
     #Se inicializan y concatenan los procesos.
     for p in prodlst + [consumidor]:

        p.start()

     for p in prodlst + [consumidor]:
        p.join()
     #Se imprime por pantalla la solución.
     print(solucion)


if __name__ == '__main__':
    main()
