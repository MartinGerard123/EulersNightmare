import sys
import math
import random
import signal
import os  # libreria todo guapa para escanear todo lo q haya en el directorio actual

# esto es una funcion para verificar que el numero obtenido no sea un falso positivo
def victoria(n, factor_encontrado, nombre_archivo=""):
    if factor_encontrado is None or factor_encontrado <= 1 or factor_encontrado >= n:
        return 
        
    if n % factor_encontrado == 0:
        d = 2
        temp_f = factor_encontrado
        while d * d <= temp_f:
            if temp_f % d == 0:
                factor_encontrado = d
                break
            d += 1
        
        p = factor_encontrado
        q = n // p
        p_menor, p_mayor = min(p, q), max(p, q)
        
        print(f"\n[================================================]")
        print(f"[+++ HACK COMPLETADO: {nombre_archivo} +++]")
        print(f"[================================================]")
        print(f"[*] (Menor): {p_menor}")
        print(f"[*] (Mayor): {p_mayor}")
        print(f"[================================================]\n")
        
        
        return True 
    return False

# (Timeouts para no pasarme la vida esperando)
class TimeoutException(Exception): pass
def manejador_timeout(signum, frame): raise TimeoutException("Timeout")
def set_timeout(segundos):
    signal.signal(signal.SIGALRM, manejador_timeout)
    signal.alarm(segundos)
def clear_timeout(): signal.alarm(0)

# (Filtros para detectar de forma temprana si es una trufa o si no, pasar a la siguiente fase)

#Primero, ver si realmente es un numero primo o no.. (a ver... se entiende que no debe serlo, pero por si acaso)
def test_miller_rabin(n, k=10):
    if n <= 1: return False
    if n in (2, 3): return True
    if n % 2 == 0: return False
    r, s = 0, n - 1
    while s % 2 == 0: r += 1; s //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x == 1 or x == n - 1: continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1: break
        else: return False
    return True
#ver si es cuadrado perfecto...
def filtro_cuadrado_cubo(n):
    raiz2 = math.isqrt(n)
    if raiz2 * raiz2 == n: return raiz2
    low, high = 1, raiz2
    while low <= high:
        mid = (low + high) // 2
        cubo = mid * mid * mid
        if cubo == n: return mid
        elif cubo < n: low = mid + 1
        else: high = mid - 1
    return None
#pruebo primos pequeños a ver si de suerte, alguno es factor del numero a destruir
def filtro_basura(n):
    primos_triviales = 2305567963945518424753102147331756070
    factor = math.gcd(n, primos_triviales)
    return factor if factor > 1 and factor != n else None

#metodo que organiza ataque, una vez leemos el .txt.. pasando primero por filtros y si
#no cae... pasandolo segun su longitud a algoritmos especificos..
def atacar_numero(N, nombre_fichero):
    bits = N.bit_length()
    print(f"\n>>> ANALIZANDO: {nombre_fichero} ({bits} bits)")
    
    # --- FASE 1: Filtros ---
    if test_miller_rabin(N): return victoria(N, N, nombre_fichero)
    raiz = filtro_cuadrado_cubo(N)
    if raiz: return victoria(N, raiz, nombre_fichero)
    f_trivial = filtro_basura(N)
    if f_trivial: return victoria(N, f_trivial, nombre_fichero)

    # --- FASE 2: Tiers ---
    try:
        if bits < 45:
            set_timeout(3)
            res = ataque_trial_division(N)
        elif bits <= 80:
            set_timeout(10) 
            res = ataque_pollard_brent(N)
        else:
            # Para números grandes
            set_timeout(5)
            res = ataque_fermat_clasico(N, 100000)
            if not res:
                clear_timeout()
                set_timeout(10)
                res = ataque_pollard_p1(N, 500000)
        
        clear_timeout()
        if res: return victoria(N, res, nombre_fichero)
    except TimeoutException:
        print(f"    [-] Saltando {nombre_fichero}: Demasiado duro.")
    
    return False

# Algoritmos que he investigado que son buenos para criptografia..
def ataque_trial_division(n):
    limite = math.isqrt(n)
    divisor = 3
    while divisor <= limite:
        if n % divisor == 0: return divisor
        divisor += 2
    return None

def ataque_pollard_brent(n):
    if n % 2 == 0: return 2
    y, c, m = random.randint(1, n-1), random.randint(1, n-1), random.randint(1, n-1)
    g, r, q = 1, 1, 1
    while g == 1:
        x = y
        for _ in range(r): y = (pow(y, 2, n) + c) % n
        k = 0
        while k < r and g == 1:
            ys = y
            for _ in range(min(m, r - k)):
                y = (pow(y, 2, n) + c) % n
                q = q * abs(x - y) % n
            g = math.gcd(q, n)
            k += m
        r *= 2
    if g == n:
        while True:
            ys = (pow(ys, 2, n) + c) % n
            g = math.gcd(abs(x - ys), n)
            if g > 1: break
    return g

def ataque_fermat_clasico(n, limite_intentos=500000):
    a = math.isqrt(n) + 1
    b2 = a*a - n
    for _ in range(limite_intentos):
        b = math.isqrt(b2)
        if b*b == b2: return a - b
        a += 1
        b2 = a*a - n
    return None

def ataque_pollard_p1(n, limite_B=500000):
    a = 2
    for j in range(2, limite_B + 1):
        a = pow(a, j, n)
        if j % 5000 == 0:
            g = math.gcd(a - 1, n)
            if 1 < g < n: return g
    g = math.gcd(a - 1, n)
    return g if 1 < g < n else None

#main del script :)
def main():
    archivos_a_procesar = []

    # Si paso un archivo como parámetro, procesa solo ese
    if len(sys.argv) == 2:
        archivos_a_procesar.append(sys.argv[1])
    else:
        # Si no, busca todos los .txt de la carpeta actual
        print("[*] Buscando 'trufas' (.txt) en la carpeta actual...")
        for f in os.listdir('.'):
            if f.endswith('.txt'):
                archivos_a_procesar.append(f)
        
        # BARAJADO ALEATORIO: Esto es simplemente para atacarlos de forma random
        #es algo totalmente quitable lvd...
        random.shuffle(archivos_a_procesar)

    if not archivos_a_procesar:
        print("[-] No se encontraron archivos .txt para procesar.")
        return

    encontrados = 0
    for ruta in archivos_a_procesar:
        try:
            with open(ruta, 'r') as f:
                texto = f.read().strip()
                # Extraer solo los dígitos del archivo
                N_str = ''.join(filter(str.isdigit, texto))
                if not N_str: continue
                N = int(N_str)
                
                if atacar_numero(N, ruta):
                    encontrados += 1
        except Exception as e:
            print(f"[-] Error con {ruta}: {e}")
            continue

    print(f"\n[!] Sesión terminada. Trufas encontradas: {encontrados}/{len(archivos_a_procesar)}")

if __name__ == "__main__":
    main()