# Laboratorio 3 · Un gate de seguridad en el pipeline del equipo

**Sesión 4 · viernes 20 de noviembre · 8:45 a 9:30 p. m. (45 min en clase; se termina en el estudio independiente) · 7,5 % de la nota**
**Entrega:** como comentario en el issue de su equipo con el enlace al pull request y a la regla. Hasta la sesión 5 con 20 % menos.

En la sesión 2 modelamos qué puede salir mal. En la 3 lo verificamos con ASVS, Semgrep y ZAP, corriéndolos a mano. Hoy la pregunta es: **¿cómo logramos que nadie vuelva a introducir esa falla sin que el pipeline lo note?** La respuesta es un gate determinista que bloquea el merge, más una regla que codifica la amenaza de su Lab 1.

Usamos **Auditgate** (`github.com/Jawy77/auditgate`): un gate que **bloquea solo lo nuevo** (compara contra el merge-base, no contra toda la deuda), con un agente de IA que comenta en el PR pero **nunca decide el merge**.

| Pieza | Quién decide | Qué hace |
|---|---|---|
| **Gate determinista** | La regla | Único check requerido. Bloquea el merge si hay un hallazgo nuevo. Siempre el mismo resultado. |
| **Triage con IA** | Nadie (solo opina) | Comenta verdadero/falso positivo, alcanzabilidad y fix. No marca checks ni aprueba. |
| **Regla con prueba** | Ustedes | Codifica un patrón (no un bug puntual) con un fixture que falla sin el control y pasa con él. |

> **Regla del laboratorio:** todo corre sobre **su** repositorio y su sandbox. El escaneo y los PR de prueba se hacen contra el repo del equipo o un fork propio, nunca contra infraestructura de la empresa o de un tercero sin autorización escrita (Ley 1273 de 2009).

## 0. Preparar (5 min)

```bash
pipx install "git+https://github.com/Jawy77/auditgate"   # trae el CLI
brew install gitleaks osv-scanner && pipx install semgrep  # las herramientas del gate
auditgate doctor                                           # revisa la instalación
```

En la VM del curso las herramientas ya están. Si falta una, ese control se omite y lo avisa; el gate nunca da un verde engañoso.

## 1. Instalar el gate en el repo del equipo (10 min)

```bash
cd su-repo
auditgate init          # elige modelo (Claude, Grok, OpenAI o compatible) o solo gate determinista
git add .github/workflows/auditgate.yml
git commit -m "ci: instala el gate de seguridad"
git push
```

En GitHub: **Settings → Branches → Branch protection** sobre `main`, con **Security Gate** como *required status check*. Sin esto el gate comenta pero no bloquea: es la pieza que convierte un reporte en un control.

**Evidencia:** el workflow commiteado y una captura de la regla de branch protection.

## 2. Un PR que el gate bloquea (10 min)

Abran una rama e introduzcan **una** falla real (la que modelaron en el Lab 1, si se puede):

```bash
git checkout -b feature/falla-demo
# agreguen, por ejemplo, un SQLi por concatenación, un secreto hardcodeado,
# o una dependencia con CVE conocida
auditgate scan          # véanlo bloquear ANTES de subir (exit 1)
git commit -am "feat: cambio con falla" && git push -u origin HEAD
gh pr create --fill
```

En el PR, segundos después: el **Security Gate** queda en rojo con el hallazgo nuevo, y el botón de merge, bloqueado.

**Evidencia:** captura del check `Security Gate` *failing* y del hallazgo nuevo.

## 3. Leer el triage y corregir (5 min)

Lean el comentario del bot de triage: ¿verdadero o falso positivo?, ¿es alcanzable?, ¿qué fix sugiere? Corrijan, hagan push y vean el gate pasar a **verde** y el merge habilitarse.

**Evidencia:** captura del comentario del triage y del gate en verde tras el fix.

## 4. Codify: la amenaza del Lab 1, vuelta regla (15 min + estudio)

Este es el corazón del laboratorio. Tomen **una** amenaza de su top 5 del Lab 1 y conviértanla en una **regla con prueba** (propia o adaptada de `src/auditgate/rules/`):

1. **El patrón, no el bug.** Escriban una regla Semgrep que reconozca el patrón inseguro (p. ej. `subprocess.$F(..., shell=True)`, SQL por f-string, `verify_signature: False`), no solo la línea concreta.
2. **Dos fixtures:** un caso vulnerable que la regla **debe** marcar y un caso seguro que **no debe** marcar (el falso positivo que hay que evitar).
3. **La prueba:** el fixture vulnerable es detectado y el seguro no. Sin el control, el PoC pasa el gate; con la regla, lo bloquea.
4. **Trazabilidad:** en el PR, liguen la regla al requisito ASVS y a la amenaza del Lab 1 que mitiga.

> Una regla sin prueba es tan peligrosa como código sin prueba: genera falsos positivos que entrenan al equipo a ignorar el gate.

## 5. ¿Qué vio el gate y qué vio el triage? (5 min)

Tres líneas en el PR o en `seguridad/lab3/README.md`: ¿qué hallazgo bloqueó el gate que una persona habría dejado pasar?, ¿el triage acertó en el verdadero/falso positivo?, ¿qué deuda vieja dejó pasar el gate por no ser nueva (y por qué está bien)?

## Entrega

En el repositorio del equipo:

1. El workflow `auditgate.yml` commiteado y la branch protection con `Security Gate` requerido (captura).
2. El **pull request** de la sección 2–3: bloqueado por el gate y luego en verde tras el fix.
3. La **regla** de la sección 4 con sus dos fixtures y la prueba que pasa.
4. Las tres líneas de reflexión de la sección 5.

Comenten el enlace al PR y a la regla en el issue de su equipo. La regla y su trazabilidad amenaza → prueba → gate son parte del proyecto integrador (Entregable 2, sesión 5).

## Rúbrica (7,5 %)

| Criterio | Peso | Sobresaliente | Aceptable | Insuficiente |
|---|---|---|---|---|
| Gate instalado y requerido | 25 % | `auditgate init` aplicado y `Security Gate` como check requerido en un PR real | Instalado pero no requerido en branch protection | Sin instalar |
| PR que bloquea y se corrige | 30 % | Un PR introduce una falla, el gate la bloquea, un commit posterior lo pasa a verde | El PR bloquea pero no se corrige, o el fix no pasa el gate | Sin PR o el gate no bloqueó |
| Regla codificada con prueba | 30 % | Regla con dos fixtures; el test falla sin el control y pasa con él; ligada a una amenaza del Lab 1 | Regla sin fixture seguro, o sin ligar a ASVS/Lab 1 | Sin regla o sin prueba |
| Trazabilidad y reflexión | 15 % | Liga gate, triage y amenaza con datos propios | Reflexión genérica | Ausente |

Los laboratorios entregados después de la sesión se reciben hasta la sesión siguiente con una penalización del 20 %.
