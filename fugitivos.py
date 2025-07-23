from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from typing import Dict, Union, List, Optional, Tuple  
from fastapi.testclient import TestClient
import unittest     #Para Tests

app = FastAPI(
    title="Más buscados del FBI - Mi_Primer_API",
)

class Fugitivo(BaseModel):
    nombre_completo: str
    delito_principal: str 
    recompensa_dolares: float 

class ActualizarEstadoFugitivo(BaseModel):
    estado: str

class RespuestaFugitivo(Fugitivo):
    id: int
    estado: str

dicNuevoEstadoF: Dict[int, Dict[str, Union[str, float, int]]] = {}
idContadorEstado: int = 0

# Métodos---------------------------------------------------------------------------------------------------------- ------------------

def getFugitivo(dicNuevo: Dict[int, Dict], idFugitivo: int) -> Optional[Dict]:
    return dicNuevo.get(idFugitivo)

def getFugitivos(dicNuevo: Dict[int, Dict], skip: int = 0, limit: int = 100) -> List[Dict]:
    todosFugitivos = list(dicNuevo.values())
    return todosFugitivos[skip : skip + limit]

def crearFugitivo(dicNuevo: Dict[int, Dict], idActualContador: int, fugitivo: Fugitivo) -> Tuple[Dict[int, Dict], int, Dict]:
    idNuevo = idActualContador + 1
    datosNuevoFugitivo = fugitivo.model_dump()
    datosNuevoFugitivo["id"] = idNuevo
    datosNuevoFugitivo["estado"] = "activo"
    dicNuevo = {**dicNuevo, idNuevo: datosNuevoFugitivo}
    return dicNuevo, idNuevo, datosNuevoFugitivo

def eliminarFugitivo(dicNuevo: Dict[int, Dict], idFugitivo: int) -> Tuple[Dict[int, Dict], bool]:
    if idFugitivo not in dicNuevo:
        return dicNuevo, False
    dicNuevo = {key: value for key, value in dicNuevo.items() if key != idFugitivo}
    return dicNuevo, True

def actualizarEstadoFugitivoFn(dicNuevo: Dict[int, Dict], idFugitivo: int, nuevo_estado: str) -> Tuple[Dict[int, Dict], Optional[Dict]]:
    if idFugitivo not in dicNuevo:
        return dicNuevo, None
    actualizarFugitivo = {**dicNuevo[idFugitivo], "estado": nuevo_estado}
    dicNuevo = {**dicNuevo, idFugitivo: actualizarFugitivo}
    return dicNuevo, actualizarFugitivo







# Endpoints---------------------------------------------------------------------------------------------------------- ------------------
#Prefiero usar el camelCase como método de escritura en los códigos, pero no se si debería cambiarlo por convencion
#response_model asegura que mi API proporcione respuestas consistentes, válidas y bien documentadas.
#status_code es para que cuando se cree un nuevo fugitivo correctamente, la API debe responder con el código 201
@app.post("/fugitivos/", response_model=RespuestaFugitivo, summary="Añadir un nuevo fugitivo", status_code=201)

def crearFugitivoEndpoint(fugitivo: Fugitivo):
    global dicNuevoEstadoF, idContadorEstado
    dicNuevo, idAcumuladorNuevo, fugitivoCreado = crearFugitivo(dicNuevo=dicNuevoEstadoF, idActualContador=idContadorEstado, fugitivo=fugitivo)
    dicNuevoEstadoF = dicNuevo
    idContadorEstado = idAcumuladorNuevo
    return RespuestaFugitivo(**fugitivoCreado)

@app.get("/fugitivos/", response_model=List[RespuestaFugitivo], summary="Listar todos los fugitivos")
def obtenerListadoDeFugitivosEndpoint(skip: int = 0, limit: int = 100):
    fugitivos = getFugitivos(dicNuevo=dicNuevoEstadoF, skip=skip, limit=limit)
    return [RespuestaFugitivo(**f) for f in fugitivos]

@app.delete("/fugitivos/{idFugitivo}", status_code=204, summary="Eliminar un fugitivo")
def eliminarFugitivoEndpoint(idFugitivo: int):
    global dicNuevoEstadoF
    dicNuevo, success = eliminarFugitivo(dicNuevo=dicNuevoEstadoF, idFugitivo=idFugitivo)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fugitivo no encontrado")
    dicNuevoEstadoF = dicNuevo
    return

@app.put("/fugitivos/{idFugitivo}/estado", response_model=RespuestaFugitivo, summary="Actualizar el estado de un fugitivo")
def actualizarEstadoFugitivoEndpoint(idFugitivo: int, actualizarEstado: ActualizarEstadoFugitivo):
    global dicNuevoEstadoF
    if actualizarEstado.estado not in ["activo", "capturado"]:      #Controlar que los datos ingresados estén correctos
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El estado debe ser 'activo' o 'capturado'")
    dicNuevo, fugitivoActualizado = actualizarEstadoFugitivoFn(dicNuevo=dicNuevoEstadoF, idFugitivo=idFugitivo, nuevo_estado=actualizarEstado.estado)
    if fugitivoActualizado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fugitivo no encontrado")
    dicNuevoEstadoF = dicNuevo
    return RespuestaFugitivo(**fugitivoActualizado)




# Tests---------------------------------------------------------------------------------------------------------- ------------------
class TestFugitivosAPI(unittest.TestCase):

    def setUp(self):
        #Creamos un cliente de prueba que se llama self.client
        self.client = TestClient(app)
        dicNuevoEstadoF.clear()
        globals()['idContadorEstado'] = 0

    def test_crearFugitivo(self):
        response = self.client.post(
            "/fugitivos/",
            json={
                "nombre_completo": "Taylor Swift",
                "delito_principal": "Roba corazones",
                "recompensa_dolares": 5000000.00
            }
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["nombre_completo"], "Taylor Swift")
        self.assertEqual(data["delito_principal"], "Roba corazones")
        self.assertEqual(data["recompensa_dolares"], 5000000.00)
        self.assertEqual(data["estado"], "activo")
        self.assertIn("id", data)

    def test_leerFugitivosCreados(self):
        self.client.post("/fugitivos/", json={
            "nombre_completo": "Jessi Uribe",
            "delito_principal": "Infiel",
            "recompensa_dolares": 20000000.00
        })
        response = self.client.get("/fugitivos/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["nombre_completo"], "Jessi Uribe")

    def test_eliminarFugitivos(self):
        create_response = self.client.post("/fugitivos/", json={
            "nombre_completo": "Terminator",
            "delito_principal": "Destrozos en la obra pública",
            "recompensa_dolares": 10000.00
        })
        idFugitivo = create_response.json()["id"]

        delete_response = self.client.delete(f"/fugitivos/{idFugitivo}")
        self.assertEqual(delete_response.status_code, 204)

        update_response = self.client.put(f"/fugitivos/{idFugitivo}/estado", json={"estado": "capturado"})
        self.assertEqual(update_response.status_code, 404)

    def test_actualizarEstadoFugitivo(self):
        create_response = self.client.post("/fugitivos/", json={
            "nombre_completo": "Batman",
            "delito_principal": "Daño en edificios",
            "recompensa_dolares": 12000.00
        })
        idFugitivo = create_response.json()["id"]
        update_response = self.client.put(f"/fugitivos/{idFugitivo}/estado", json={"estado": "capturado"})
        self.assertEqual(update_response.status_code, 200)
        updated_data = update_response.json()
        self.assertEqual(updated_data["estado"], "capturado")
