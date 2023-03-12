
#PRÁCTICA 1. Parte opcional.
#LUCÍA ROLDÁN RODRÍGUEZ.

from multiprocessing import Process,Manager
from multiprocessing import  Semaphore, BoundedSemaphore
from multiprocessing import current_process
from multiprocessing import  Array
from time import sleep
import random

NPROD = 4 # número de productores.
M = 3 # capacidad del buffer.
N = 5 # número de veces que produce cada productor.

#La función new_data genera un valor mayor que el último producido, en un rango de 10 unidades.
def new_data(ultimo_valor):
    a = random.randint(1,10)
    return (ultimo_valor + a)
# La función delay tiene como objetivo simular un tiempo de producción y consumición.
def delay(factor = 3):
    sleep(random.random()/factor)

def producer(buffer,non_empty,empty,M):
    indice_escritura= 0 #se inicializa en 0 la posición de escritura en el buffer.
    ultimo_valor = 0 #en esta variable se almacenará el último valor producido por el productor
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        empty.acquire()#se va a aumentar en uno el número de elementos almacenados en el buffer.
        #Por tanto se comprueba si hay hueco.
        ultimo_valor = new_data(ultimo_valor) #se genera el nuevo valor.
        buffer[indice_escritura] = ultimo_valor #se almacena dicho valor en la posición correspondiente.
        indice_escritura =(indice_escritura + 1) % M # se aumenta en 1 (módulo la capacidad del buffer)
        print (f"producer {current_process().name} ha almacenado {ultimo_valor}")
        buffer_actual = [i for i in buffer] #se devuelve por pantalla el estado del buffer modificado.
        print(f"así se encuentra el buffer de {current_process().name}: {buffer_actual}")
        non_empty.release() #se aumenta en uno la capacidad del semáforo encargado de regular 
        # la existencia de valores en el buffer antes de consumir.
    # Por último se repite el proceso añadiendo un -1 como símbolo de finalización de la produción.
    empty.acquire()
    buffer[indice_escritura] = -1
    print (f"producer {current_process().name} ha terminado de producir")
    non_empty.release()
    
#La función minimo devuelve el mínimo valor distinto de -1  en una lista
#así como el índice de la posición en que se encuentra.        
def minimo(storage):
    indice = 0
    valor = storage[0]
    #Se asegura de que no se haya inicializado en -1 
    while valor == -1 :
        indice +=1
        valor = storage[indice]
    #se comprueba si existe un valor menor diferente de -1 a lo largo de 
    # la lista en cuyo caso se actualiza el índice y el valor.
    for k in range(1,len(storage)):
        if storage[k] < valor and storage[k] != -1 :
            valor = storage[k]
            indice = k
    return(indice,valor)
    
# la función stiLl_producing sirve para comprobar si algún productor sigue produciendo
# para ello comprueba que la lista pasada por parámetro no esté confomrada exclusivamente
# por -1.
def still_producing(storage):
    for k in range(len(storage)):
        if storage[k] != -1:
            return(True)
    return(False)
        
    
def consumer(buffers, sol,non_empty_list,empty_list,lectura,M):
    #Se espera hasta que todas la posiciones de los productores hayan sido cubiertas.
    for i in range(NPROD):
        non_empty_list[i].acquire()
    #en la variable valores almacenamos una lista con las menores posiciones
    # de cada buffer, es decir, el valor que se encuentra en su índice de lectura.   
    valores=[]
    for i in range(len(buffers)):
        valores.append(buffers[i][lectura[i]])
        
    # mientras haya algún productor que siga produciendo se entrará en el bucle
    while still_producing(valores):
        indice = minimo(valores)[0] # indice del productor con el mínimo elemento
        valor = minimo(valores)[1] # valor del elemento mínimo
        sol.append(valor) #añadimos el valor a la solución
        buffers[indice][lectura[indice]] = -2 #se actualiza la posición como vacía en dicho productor.
        lectura[indice] = (lectura[indice]+1)%M 
        # se aumenta en uno (módulo la capacidad del buffer) el índice de lectura del productor del cúal se ha consumido un valor. 
        print (f" consumido {valor} del productor {indice}")
        # se aumenta en uno la capacidad del semáforo (del proceso del cual se ha consumido)
        # que se encarga de comprobrar la existencia de posiciones libres en los buffers antes de producir.
        empty_list[indice].release()
        delay()
        # se reduce en uno la capacidad del semáforo encargado de comprobrar
        # que existen valores almacenados en el buffer de dicho productor.
        non_empty_list[indice].acquire()
        # se actualiza el valor sustraido de valores por el siguiente correspondiente en el buffer de dicho productor. 
        valores[indice] = buffers[indice][lectura[indice]]
        
            
def main():
     # Se crea un array de capacidad M para cada productor.
     buffers = [Array('i',M) for j in range(NPROD)]
     # Se inicializan los buffers con posiciones vacías.
     for buffer in buffers:
         for j in range(M):
             buffer[j] = -2 
             
     # Se almacena en un array el índice de lectura de cada buffer
     # el cual recibirá el consumidor para saber de dónde debe leer ya que 
     # se va a trabajar con buffers circulares.
     posiciones_lectura_buffer = Array('i',NPROD)
     # Se inicializan las posiciones de lectura en la primera posición.
     for i in range(NPROD):
         posiciones_lectura_buffer[i] = 0 
         
     # Solución es la lista donde se irán almacenando de forma ordenada
     # los valores producidos.
     manager = Manager()
     solucion= manager.list()
     
     # Se crea una lista de semáforos que regularán que cuando vaya a consumir el 
     # consumidor exista un valor producido por todos los productores que no
     # hayan terminado de producir.
     non_empty_list = [Semaphore(0) for i in range(NPROD)] 
     
     # Se crea una lista de semáforos encargados de regular que no se produzca 
     # si no hay hueco puesto que supondría una pérdida de información.
     empty_list = [BoundedSemaphore(M) for i in range(NPROD)]   
     
     # Se crean NPROD procesos, cada uno con su buffer, sus semáforos 
     # correspondientes y la capacidad de almacenamiento de los buffers.     .
     prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(buffers[i],non_empty_list[i], empty_list[i],M))
                for i in range(NPROD) ]
     #Se crea un consumidor que recibe por parámetros, la lista de buffers, la lista solución,
     # ambas listas de semáforos, las posiciones de lectura y la capacidad de alamacenamiento de los buffers. 
     consumidor = Process(target=consumer,args=(buffers,solucion,non_empty_list, empty_list, posiciones_lectura_buffer,M))
     #Se inicializan y concatenan los procesos.
     for p in prodlst + [consumidor]:
         
        p.start()

     for p in prodlst + [consumidor]:
        p.join()
     #Se imprime por pantalla la solución. 
     print(solucion)
    
    
if __name__ == '__main__':
    main()

    
    
