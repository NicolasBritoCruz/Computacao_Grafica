# -*- coding: utf-8 -*-

import math
import colorsys

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# ---------------------------------------------------------------------------
# 1. DEFINICAO DOS SOLIDOS (vertices + faces triangulares)
# ---------------------------------------------------------------------------

# --- Tetraedro: 4 vertices, 4 faces --------------------------------------
tetraedro_vertices = [
    [ 1,  1,  1],
    [-1, -1,  1],
    [-1,  1, -1],
    [ 1, -1, -1],
]
tetraedro_faces = [
    (0, 1, 2),
    (0, 3, 1),
    (0, 2, 3),
    (1, 3, 2),
]

# --- Octaedro: 6 vertices, 8 faces ----------------------------------------
octaedro_vertices = [
    [ 1,  0,  0],
    [-1,  0,  0],
    [ 0,  1,  0],
    [ 0, -1,  0],
    [ 0,  0,  1],
    [ 0,  0, -1],
]
octaedro_faces = [
    (0, 2, 4), (2, 1, 4),
    (1, 3, 4), (3, 0, 4),
    (0, 5, 2), (2, 5, 1),
    (1, 5, 3), (3, 5, 0),
]

# --- Icosaedro: 12 vertices, 20 faces (usa a razao aurea phi) -------------
_phi = (1 + math.sqrt(5)) / 2

icosaedro_vertices = [
    [-1,  _phi, 0], [ 1,  _phi, 0], [-1, -_phi, 0], [ 1, -_phi, 0],
    [0, -1,  _phi], [0,  1,  _phi], [0, -1, -_phi], [0,  1, -_phi],
    [ _phi, 0, -1], [ _phi, 0,  1], [-_phi, 0, -1], [-_phi, 0,  1],
]
icosaedro_faces = [
    (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
    (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
    (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
    (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
]


def normalizar_escala(vertices, raio_alvo=1.6):
    """Reescala os vertices para que o solido caiba sempre no mesmo raio
    visual, ja que cada conjunto de coordenadas tem uma "distancia da
    origem" diferente (tetraedro, octaedro e icosaedro nao nascem do
    mesmo tamanho). Sem isso, o solido "pula" de tamanho ao trocar."""
    maior_distancia = max(math.sqrt(x * x + y * y + z * z) for x, y, z in vertices)
    fator = raio_alvo / maior_distancia
    return [[x * fator, y * fator, z * fator] for x, y, z in vertices]


def gerar_cores(quantidade_faces):
    """Gera uma cor (RGB) diferente para cada face, distribuindo o matiz
    (hue) igualmente no circulo de cores. Funciona para qualquer numero
    de faces (4, 8 ou 20), sem precisar listar cores na mao."""
    cores = []
    for i in range(quantidade_faces):
        matiz = i / quantidade_faces
        r, g, b = colorsys.hsv_to_rgb(matiz, 0.75, 0.95)
        cores.append((r, g, b))
    return cores


# Lista dos solidos disponiveis: cada item guarda nome, vertices (ja
# normalizados) e faces. E o que permite trocar de solido so mudando um
# indice, reaproveitando a mesma funcao de desenho para os tres.
SOLIDOS = [
    {
        "nome": "Tetraedro",
        "vertices": normalizar_escala(tetraedro_vertices),
        "faces": tetraedro_faces,
    },
    {
        "nome": "Octaedro",
        "vertices": normalizar_escala(octaedro_vertices),
        "faces": octaedro_faces,
    },
    {
        "nome": "Icosaedro",
        "vertices": normalizar_escala(icosaedro_vertices),
        "faces": icosaedro_faces,
    },
]
# Pre-computa as cores de cada face de cada solido uma unica vez.
for solido in SOLIDOS:
    solido["cores"] = gerar_cores(len(solido["faces"]))


# ---------------------------------------------------------------------------
# 2. ESTADO GLOBAL (posicao do solido atual + angulos de rotacao)
# ---------------------------------------------------------------------------

indice_solido_atual = 0

angulo_rotacao_x = 0.0
angulo_rotacao_y = 0.0
VELOCIDADE_ROTACAO_X = 0.3   # graus por quadro
VELOCIDADE_ROTACAO_Y = 0.5   # graus por quadro

LARGURA_JANELA = 900
ALTURA_JANELA = 700


# ---------------------------------------------------------------------------
# 3. FUNCOES DE DESENHO
# ---------------------------------------------------------------------------

def desenhar_solido(vertices, faces, cores):
    """Desenha um solido qualquer a partir de suas listas de vertices e
    faces, usando GL_TRIANGLES. Essa funcao e generica: e a mesma para
    o tetraedro, o octaedro e o icosaedro."""
    glBegin(GL_TRIANGLES)
    for face, cor in zip(faces, cores):
        glColor3f(*cor)
        for indice_vertice in face:
            glVertex3fv(vertices[indice_vertice])
    glEnd()


def desenhar_eixos(tamanho=2.5):
    """Desenha os eixos principais X (vermelho), Y (verde) e Z (azul)
    como referencia visual durante a rotacao."""
    glLineWidth(2.0)
    glBegin(GL_LINES)

    # Eixo X - vermelho
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(-tamanho, 0.0, 0.0)
    glVertex3f(tamanho, 0.0, 0.0)

    # Eixo Y - verde
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0.0, -tamanho, 0.0)
    glVertex3f(0.0, tamanho, 0.0)

    # Eixo Z - azul
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, -tamanho)
    glVertex3f(0.0, 0.0, tamanho)

    glEnd()


def desenhar_texto_hud(texto, x, y):
    """Escreve um texto simples na tela (HUD) informando qual solido
    esta sendo exibido no momento."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, LARGURA_JANELA, 0, ALTURA_JANELA)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for caractere in texto:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(caractere))
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


# ---------------------------------------------------------------------------
# 4. CALLBACKS DO GLUT
# ---------------------------------------------------------------------------

def exibir():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Afasta a "camera" para conseguir ver o solido inteiro.
    glTranslatef(0.0, 0.0, -6.0)

    # Aplica a rotacao continua (eixos e solido giram juntos, servindo
    # o eixo como referencia de como o solido esta orientado).
    glRotatef(angulo_rotacao_x, 1.0, 0.0, 0.0)
    glRotatef(angulo_rotacao_y, 0.0, 1.0, 0.0)

    desenhar_eixos()

    solido = SOLIDOS[indice_solido_atual]
    desenhar_solido(solido["vertices"], solido["faces"], solido["cores"])

    nome_exibicao = "%s (%d/%d) - use as setas para trocar" % (
        solido["nome"], indice_solido_atual + 1, len(SOLIDOS),
    )
    desenhar_texto_hud(nome_exibicao, 20, ALTURA_JANELA - 30)

    glutSwapBuffers()


def animar():
    """Atualiza os angulos de rotacao a cada quadro, como no exemplo
    do cubo, e pede para o GLUT redesenhar a tela."""
    global angulo_rotacao_x, angulo_rotacao_y
    angulo_rotacao_x = (angulo_rotacao_x + VELOCIDADE_ROTACAO_X) % 360
    angulo_rotacao_y = (angulo_rotacao_y + VELOCIDADE_ROTACAO_Y) % 360
    glutPostRedisplay()


def teclado_especial(tecla, x, y):
    """Troca o solido atual usando as setas do teclado."""
    global indice_solido_atual
    if tecla == GLUT_KEY_RIGHT:
        indice_solido_atual = (indice_solido_atual + 1) % len(SOLIDOS)
    elif tecla == GLUT_KEY_LEFT:
        indice_solido_atual = (indice_solido_atual - 1) % len(SOLIDOS)
    glutPostRedisplay()


def teclado(tecla, x, y):
    """ESC fecha o programa."""
    if tecla == b"\x1b":
        glutLeaveMainLoop()


def redimensionar(largura, altura):
    global LARGURA_JANELA, ALTURA_JANELA
    LARGURA_JANELA, ALTURA_JANELA = largura, max(altura, 1)

    glViewport(0, 0, LARGURA_JANELA, ALTURA_JANELA)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, LARGURA_JANELA / float(ALTURA_JANELA), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)


# ---------------------------------------------------------------------------
# 5. INICIALIZACAO
# ---------------------------------------------------------------------------

def inicializar_opengl():
    glClearColor(0.08, 0.08, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(LARGURA_JANELA, ALTURA_JANELA)
    glutCreateWindow(b"Solidos de Platao - Tetraedro / Octaedro / Icosaedro")

    inicializar_opengl()

    glutDisplayFunc(exibir)
    glutIdleFunc(animar)
    glutReshapeFunc(redimensionar)
    glutSpecialFunc(teclado_especial)
    glutKeyboardFunc(teclado)

    glutMainLoop()


if __name__ == "__main__":
    main()
