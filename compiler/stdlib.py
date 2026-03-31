# compiler/stdlib.py
# Mesa Language v2.2.0 - Standard Library COMPLETA
# Filesystem, HTTP Client+Server, JSON, Regex, Crypto,
# Database, Concurrencia, Testing avanzado

import os
import sys
import json
import re
import math
import time
import random
import hashlib
import hmac
import base64
import threading
import queue
import socket
import sqlite3
import csv
import urllib.request
import urllib.parse
import urllib.error
import ssl
import io
import struct
import zlib
import gzip
import shutil
import subprocess
import signal
import traceback
import datetime
import uuid
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import reduce

from .interpreter import MesaRuntimeError, MesaFunc, MesaResult


# ============================================================
# FILESYSTEM
# ============================================================

class MesaFilesystem:

    @staticmethod
    def register(env, define, interpreter):

        def archivo_leer(path, encoding='utf-8'):
            try:
                with open(str(path), 'r', encoding=encoding) as f:
                    return f.read()
            except FileNotFoundError:
                raise MesaRuntimeError(f"Archivo no encontrado: '{path}'")
            except PermissionError:
                raise MesaRuntimeError(f"Sin permiso para leer: '{path}'")
            except Exception as e:
                raise MesaRuntimeError(f"Error al leer archivo: {e}")

        define('archivo_leer', archivo_leer)
        define('file_read', archivo_leer)
        define('leer_archivo', archivo_leer)
        define('read_file', archivo_leer)

        def archivo_lineas(path, encoding='utf-8'):
            try:
                with open(str(path), 'r', encoding=encoding) as f:
                    return [line.rstrip('\n').rstrip('\r') for line in f.readlines()]
            except FileNotFoundError:
                raise MesaRuntimeError(f"Archivo no encontrado: '{path}'")
            except Exception as e:
                raise MesaRuntimeError(f"Error al leer lineas: {e}")

        define('archivo_lineas', archivo_lineas)
        define('file_lines', archivo_lineas)
        define('leer_lineas', archivo_lineas)
        define('read_lines', archivo_lineas)

        def archivo_leer_bytes(path):
            try:
                with open(str(path), 'rb') as f:
                    return list(f.read())
            except FileNotFoundError:
                raise MesaRuntimeError(f"Archivo no encontrado: '{path}'")
            except Exception as e:
                raise MesaRuntimeError(f"Error al leer bytes: {e}")

        define('archivo_leer_bytes', archivo_leer_bytes)
        define('file_read_bytes', archivo_leer_bytes)
        define('read_bytes', archivo_leer_bytes)

        def archivo_escribir(path, contenido, encoding='utf-8'):
            try:
                dir_path = os.path.dirname(str(path))
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                with open(str(path), 'w', encoding=encoding) as f:
                    f.write(str(contenido))
                return True
            except PermissionError:
                raise MesaRuntimeError(f"Sin permiso para escribir: '{path}'")
            except Exception as e:
                raise MesaRuntimeError(f"Error al escribir archivo: {e}")

        define('archivo_escribir', archivo_escribir)
        define('file_write', archivo_escribir)
        define('escribir_archivo', archivo_escribir)
        define('write_file', archivo_escribir)

        def archivo_agregar(path, contenido, encoding='utf-8'):
            try:
                dir_path = os.path.dirname(str(path))
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                with open(str(path), 'a', encoding=encoding) as f:
                    f.write(str(contenido))
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error al agregar: {e}")

        define('archivo_agregar', archivo_agregar)
        define('file_append', archivo_agregar)
        define('agregar_archivo', archivo_agregar)
        define('append_file', archivo_agregar)

        def archivo_escribir_bytes(path, data):
            try:
                dir_path = os.path.dirname(str(path))
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                if isinstance(data, list):
                    data = bytes(data)
                with open(str(path), 'wb') as f:
                    f.write(data)
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error al escribir bytes: {e}")

        define('archivo_escribir_bytes', archivo_escribir_bytes)
        define('file_write_bytes', archivo_escribir_bytes)
        define('write_bytes', archivo_escribir_bytes)

        def archivo_existe(path):
            return os.path.exists(str(path))

        define('archivo_existe', archivo_existe)
        define('file_exists', archivo_existe)
        define('existe', archivo_existe)
        define('exists', archivo_existe)

        def es_archivo(path):
            return os.path.isfile(str(path))

        def es_directorio(path):
            return os.path.isdir(str(path))

        define('es_archivo', es_archivo)
        define('is_file', es_archivo)
        define('es_directorio', es_directorio)
        define('is_dir', es_directorio)
        define('is_directory', es_directorio)

        def archivo_eliminar(path):
            try:
                p = str(path)
                if os.path.isfile(p):
                    os.remove(p)
                    return True
                elif os.path.isdir(p):
                    shutil.rmtree(p)
                    return True
                else:
                    raise MesaRuntimeError(f"No existe: '{path}'")
            except PermissionError:
                raise MesaRuntimeError(f"Sin permiso: '{path}'")
            except Exception as e:
                raise MesaRuntimeError(f"Error al eliminar: {e}")

        define('archivo_eliminar', archivo_eliminar)
        define('file_delete', archivo_eliminar)
        define('eliminar', archivo_eliminar)
        define('delete_file', archivo_eliminar)
        define('borrar', archivo_eliminar)

        def archivo_renombrar(origen, destino):
            try:
                os.rename(str(origen), str(destino))
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error al renombrar: {e}")

        define('archivo_renombrar', archivo_renombrar)
        define('file_rename', archivo_renombrar)
        define('renombrar', archivo_renombrar)
        define('rename', archivo_renombrar)
        define('mover', archivo_renombrar)
        define('move', archivo_renombrar)

        def archivo_copiar(origen, destino):
            try:
                shutil.copy2(str(origen), str(destino))
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error al copiar: {e}")

        define('archivo_copiar', archivo_copiar)
        define('file_copy', archivo_copiar)
        define('copiar_archivo', archivo_copiar)
        define('copy_file', archivo_copiar)

        def archivo_tamanio(path):
            try:
                return os.path.getsize(str(path))
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('archivo_tamaño', archivo_tamanio)
        define('archivo_tamanio', archivo_tamanio)
        define('file_size', archivo_tamanio)

        def archivo_info(path):
            try:
                p = str(path)
                stat = os.stat(p)
                return {
                    'nombre': os.path.basename(p),
                    'ruta': os.path.abspath(p),
                    'tamaño': stat.st_size,
                    'es_archivo': os.path.isfile(p),
                    'es_directorio': os.path.isdir(p),
                    'modificado': stat.st_mtime,
                    'creado': stat.st_ctime,
                    'extension': os.path.splitext(p)[1],
                }
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('archivo_info', archivo_info)
        define('file_info', archivo_info)

        def crear_directorio(path):
            try:
                os.makedirs(str(path), exist_ok=True)
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('crear_directorio', crear_directorio)
        define('create_dir', crear_directorio)
        define('mkdir', crear_directorio)

        def listar_directorio(path='.'):
            try:
                return os.listdir(str(path))
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('listar_directorio', listar_directorio)
        define('list_dir', listar_directorio)
        define('listar', listar_directorio)
        define('ls', listar_directorio)

        def listar_todo(path='.', extension=None):
            try:
                result = []
                for root, dirs, files in os.walk(str(path)):
                    for f in files:
                        full = os.path.join(root, f)
                        if extension is None or f.endswith(str(extension)):
                            result.append(full)
                return result
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('listar_todo', listar_todo)
        define('list_all', listar_todo)
        define('walk', listar_todo)
        define('glob', listar_todo)

        def ruta_unir(*parts):
            return os.path.join(*[str(p) for p in parts])

        def ruta_absoluta(path):
            return os.path.abspath(str(path))

        def ruta_nombre(path):
            return os.path.basename(str(path))

        def ruta_directorio(path):
            return os.path.dirname(str(path))

        def ruta_extension(path):
            return os.path.splitext(str(path))[1]

        def ruta_sin_extension(path):
            return os.path.splitext(str(path))[0]

        define('ruta_unir', ruta_unir)
        define('path_join', ruta_unir)
        define('ruta_absoluta', ruta_absoluta)
        define('path_abs', ruta_absoluta)
        define('ruta_nombre', ruta_nombre)
        define('path_name', ruta_nombre)
        define('basename', ruta_nombre)
        define('ruta_directorio', ruta_directorio)
        define('path_dir', ruta_directorio)
        define('dirname', ruta_directorio)
        define('ruta_extension', ruta_extension)
        define('path_ext', ruta_extension)
        define('ruta_sin_extension', ruta_sin_extension)
        define('path_stem', ruta_sin_extension)

        def directorio_actual():
            return os.getcwd()

        def cambiar_directorio(path):
            try:
                os.chdir(str(path))
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('directorio_actual', directorio_actual)
        define('cwd', directorio_actual)
        define('current_dir', directorio_actual)
        define('cambiar_directorio', cambiar_directorio)
        define('chdir', cambiar_directorio)
        define('cd', cambiar_directorio)

        def es_legible(path):
            return os.access(str(path), os.R_OK)

        def es_escribible(path):
            return os.access(str(path), os.W_OK)

        define('es_legible', es_legible)
        define('is_readable', es_legible)
        define('es_escribible', es_escribible)
        define('is_writable', es_escribible)


# ============================================================
# HTTP CLIENT
# ============================================================

class MesaHTTP:

    _ssl_context = None

    @classmethod
    def _get_ssl_context(cls):
        if cls._ssl_context is None:
            cls._ssl_context = ssl.create_default_context()
            cls._ssl_context.check_hostname = False
            cls._ssl_context.verify_mode = ssl.CERT_NONE
        return cls._ssl_context

    @staticmethod
    def register(env, define, interpreter):

        def _make_request(url, method='GET', data=None, headers=None, json_data=None, timeout=30):
            try:
                url = str(url)
                req_headers = {'User-Agent': 'Mesa-Language/2.2.0', 'Accept': '*/*'}
                if headers and isinstance(headers, dict):
                    req_headers.update(headers)

                body = None
                if json_data is not None:
                    body = json.dumps(MesaJSON._mesa_to_python(json_data)).encode('utf-8')
                    req_headers['Content-Type'] = 'application/json'
                elif data is not None:
                    if isinstance(data, dict):
                        body = urllib.parse.urlencode(data).encode('utf-8')
                        req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    elif isinstance(data, str):
                        body = data.encode('utf-8')

                req = urllib.request.Request(url, data=body, headers=req_headers, method=method.upper())
                ctx = MesaHTTP._get_ssl_context()
                response = urllib.request.urlopen(req, timeout=int(timeout), context=ctx)
                resp_body = response.read().decode('utf-8', errors='replace')

                return {
                    'status': response.getcode(),
                    'codigo': response.getcode(),
                    'body': resp_body,
                    'cuerpo': resp_body,
                    'headers': dict(response.headers),
                    'cabeceras': dict(response.headers),
                    'ok': 200 <= response.getcode() < 300,
                    'url': response.geturl(),
                }
            except urllib.error.HTTPError as e:
                error_body = ''
                try:
                    error_body = e.read().decode('utf-8', errors='replace')
                except:
                    pass
                return {
                    'status': e.code, 'codigo': e.code,
                    'body': error_body, 'cuerpo': error_body,
                    'headers': dict(e.headers) if e.headers else {},
                    'cabeceras': dict(e.headers) if e.headers else {},
                    'ok': False, 'error': str(e.reason), 'url': url,
                }
            except urllib.error.URLError as e:
                raise MesaRuntimeError(f"Error de conexion: {e.reason}")
            except Exception as e:
                raise MesaRuntimeError(f"Error HTTP: {e}")

        def http_get(url, headers=None, timeout=30):
            return _make_request(url, 'GET', headers=headers, timeout=timeout)

        define('http_get', http_get)
        define('http_obtener', http_get)

        def http_post(url, data=None, headers=None, timeout=30):
            jd = None
            pd = None
            if isinstance(data, (dict, list)):
                jd = data
            else:
                pd = data
            return _make_request(url, 'POST', data=pd, json_data=jd, headers=headers, timeout=timeout)

        define('http_post', http_post)
        define('http_enviar', http_post)

        def http_put(url, data=None, headers=None, timeout=30):
            jd = None
            pd = None
            if isinstance(data, (dict, list)):
                jd = data
            else:
                pd = data
            return _make_request(url, 'PUT', data=pd, json_data=jd, headers=headers, timeout=timeout)

        define('http_put', http_put)
        define('http_actualizar', http_put)

        def http_delete(url, headers=None, timeout=30):
            return _make_request(url, 'DELETE', headers=headers, timeout=timeout)

        define('http_delete', http_delete)
        define('http_eliminar', http_delete)

        def http_patch(url, data=None, headers=None, timeout=30):
            jd = None
            pd = None
            if isinstance(data, (dict, list)):
                jd = data
            else:
                pd = data
            return _make_request(url, 'PATCH', data=pd, json_data=jd, headers=headers, timeout=timeout)

        define('http_patch', http_patch)

        def http_head(url, headers=None, timeout=30):
            return _make_request(url, 'HEAD', headers=headers, timeout=timeout)

        define('http_head', http_head)

        def http_descargar(url, destino, timeout=60):
            try:
                ctx = MesaHTTP._get_ssl_context()
                req = urllib.request.Request(str(url), headers={'User-Agent': 'Mesa-Language/2.2.0'})
                response = urllib.request.urlopen(req, timeout=int(timeout), context=ctx)
                data = response.read()
                dir_path = os.path.dirname(str(destino))
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                with open(str(destino), 'wb') as f:
                    f.write(data)
                return {'ok': True, 'tamaño': len(data), 'size': len(data), 'ruta': os.path.abspath(str(destino))}
            except Exception as e:
                raise MesaRuntimeError(f"Error al descargar: {e}")

        define('http_descargar', http_descargar)
        define('http_download', http_descargar)
        define('descargar', http_descargar)
        define('download', http_descargar)

        def http_json(url, headers=None, timeout=30):
            resp = http_get(url, headers=headers, timeout=timeout)
            if resp['ok']:
                try:
                    resp['json'] = json.loads(resp['body'])
                    resp['datos'] = resp['json']
                except:
                    resp['json'] = None
                    resp['datos'] = None
            return resp

        define('http_json', http_json)
        define('fetch_json', http_json)
        define('obtener_json', http_json)

        def url_encode(text):
            return urllib.parse.quote(str(text))

        def url_decode(text):
            return urllib.parse.unquote(str(text))

        def url_params(params):
            if isinstance(params, dict):
                return urllib.parse.urlencode(params)
            return str(params)

        define('url_encode', url_encode)
        define('url_codificar', url_encode)
        define('url_decode', url_decode)
        define('url_decodificar', url_decode)
        define('url_params', url_params)
        define('url_parametros', url_params)


# ============================================================
# HTTP SERVER
# ============================================================

class MesaHTTPServer:

    @staticmethod
    def register(env, define, interpreter):

        _servers = {}
        _routes = {'GET': {}, 'POST': {}, 'PUT': {}, 'DELETE': {}, 'PATCH': {}}
        _static_dir = None
        _middleware = []

        def _call_mesa_func(func, args):
            if isinstance(func, MesaFunc):
                return interpreter._call_func(func, args)
            elif callable(func):
                return func(*args)
            return None

        class MesaHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def _get_body(self):
                length = int(self.headers.get('Content-Length', 0))
                if length > 0:
                    return self.rfile.read(length).decode('utf-8', errors='replace')
                return ''

            def _make_request_obj(self):
                parsed = urllib.parse.urlparse(self.path)
                query = dict(urllib.parse.parse_qs(parsed.query))
                for k in query:
                    if len(query[k]) == 1:
                        query[k] = query[k][0]
                body_raw = self._get_body()
                body_parsed = None
                ct = self.headers.get('Content-Type', '')
                if 'json' in ct:
                    try:
                        body_parsed = json.loads(body_raw)
                    except:
                        body_parsed = body_raw
                else:
                    body_parsed = body_raw

                return {
                    'method': self.command,
                    'metodo': self.command,
                    'path': parsed.path,
                    'ruta': parsed.path,
                    'query': query,
                    'params': query,
                    'parametros': query,
                    'body': body_parsed,
                    'cuerpo': body_parsed,
                    'body_raw': body_raw,
                    'headers': dict(self.headers),
                    'cabeceras': dict(self.headers),
                }

            def _send_response(self, result):
                if result is None:
                    self.send_response(204)
                    self.end_headers()
                    return

                if isinstance(result, dict):
                    status = result.get('status', result.get('codigo', 200))
                    headers = result.get('headers', result.get('cabeceras', {}))
                    body = result.get('body', result.get('cuerpo', ''))
                    content_type = result.get('content_type', result.get('tipo', 'text/html'))

                    self.send_response(int(status))
                    self.send_header('Content-Type', content_type)
                    if isinstance(headers, dict):
                        for k, v in headers.items():
                            if k.lower() not in ('content-type',):
                                self.send_header(str(k), str(v))
                    self.end_headers()

                    if isinstance(body, (dict, list)):
                        self.wfile.write(json.dumps(body, ensure_ascii=False).encode('utf-8'))
                    else:
                        self.wfile.write(str(body).encode('utf-8'))
                elif isinstance(result, str):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(result.encode('utf-8'))
                elif isinstance(result, (int, float)):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(str(result).encode('utf-8'))
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(MesaJSON._mesa_to_python(result), ensure_ascii=False).encode('utf-8'))

            def _handle_method(self, method):
                req = self._make_request_obj()

                for mw in _middleware:
                    try:
                        r = _call_mesa_func(mw, [req])
                        if r is not None and isinstance(r, dict) and 'status' in r:
                            self._send_response(r)
                            return
                    except:
                        pass

                routes = _routes.get(method, {})
                path = urllib.parse.urlparse(self.path).path

                handler = routes.get(path)
                if handler is None:
                    for pattern, h in routes.items():
                        if ':' in pattern:
                            p_parts = pattern.split('/')
                            r_parts = path.split('/')
                            if len(p_parts) == len(r_parts):
                                params = {}
                                match = True
                                for pp, rp in zip(p_parts, r_parts):
                                    if pp.startswith(':'):
                                        params[pp[1:]] = rp
                                    elif pp != rp:
                                        match = False
                                        break
                                if match:
                                    req['params'].update(params)
                                    req['parametros'].update(params)
                                    handler = h
                                    break

                if handler is None and _static_dir:
                    file_path = os.path.join(_static_dir, path.lstrip('/'))
                    if os.path.isfile(file_path):
                        try:
                            mime = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                            with open(file_path, 'rb') as f:
                                content = f.read()
                            self.send_response(200)
                            self.send_header('Content-Type', mime)
                            self.end_headers()
                            self.wfile.write(content)
                            return
                        except:
                            pass

                if handler is None:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    resp = json.dumps({'error': 'No encontrado', 'ruta': path})
                    self.wfile.write(resp.encode('utf-8'))
                    return

                try:
                    result = _call_mesa_func(handler, [req])
                    self._send_response(result)
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    resp = json.dumps({'error': str(e)})
                    self.wfile.write(resp.encode('utf-8'))

            def do_GET(self):
                self._handle_method('GET')

            def do_POST(self):
                self._handle_method('POST')

            def do_PUT(self):
                self._handle_method('PUT')

            def do_DELETE(self):
                self._handle_method('DELETE')

            def do_PATCH(self):
                self._handle_method('PATCH')

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,PATCH,OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                self.end_headers()

        def ruta(method, path, handler):
            m = str(method).upper()
            if m not in _routes:
                _routes[m] = {}
            _routes[m][str(path)] = handler
            return True

        define('ruta', ruta)
        define('route', ruta)

        def ruta_get(path, handler):
            return ruta('GET', path, handler)

        def ruta_post(path, handler):
            return ruta('POST', path, handler)

        def ruta_put(path, handler):
            return ruta('PUT', path, handler)

        def ruta_delete(path, handler):
            return ruta('DELETE', path, handler)

        define('ruta_get', ruta_get)
        define('route_get', ruta_get)
        define('ruta_post', ruta_post)
        define('route_post', ruta_post)
        define('ruta_put', ruta_put)
        define('route_put', ruta_put)
        define('ruta_delete', ruta_delete)
        define('route_delete', ruta_delete)

        def middleware(func):
            _middleware.append(func)
            return True

        define('middleware', middleware)

        def estatico(directory):
            nonlocal _static_dir
            _static_dir = str(directory)
            return True

        define('estatico', estatico)
        define('static', estatico)
        define('archivos_estaticos', estatico)
        define('static_files', estatico)

        def respuesta(body, status=200, content_type='text/html'):
            return {'body': body, 'cuerpo': body, 'status': int(status), 'codigo': int(status), 'content_type': str(content_type), 'tipo': str(content_type), 'headers': {}}

        define('respuesta', respuesta)
        define('response', respuesta)

        def respuesta_json(data, status=200):
            return {'body': MesaJSON._mesa_to_python(data), 'cuerpo': data, 'status': int(status), 'codigo': int(status), 'content_type': 'application/json', 'tipo': 'application/json', 'headers': {}}

        define('respuesta_json', respuesta_json)
        define('response_json', respuesta_json)
        define('json_response', respuesta_json)

        def respuesta_html(html, status=200):
            return respuesta(str(html), status, 'text/html; charset=utf-8')

        define('respuesta_html', respuesta_html)
        define('response_html', respuesta_html)
        define('html_response', respuesta_html)

        def redirigir(url, status=302):
            return {'body': '', 'status': int(status), 'content_type': 'text/html', 'headers': {'Location': str(url)}}

        define('redirigir', redirigir)
        define('redirect', redirigir)

        def servidor_iniciar(puerto=8080, host='0.0.0.0'):
            puerto = int(puerto)
            host = str(host)
            server = HTTPServer((host, puerto), MesaHandler)
            _servers[puerto] = server
            print(f"🌐 Servidor Mesa escuchando en http://{host}:{puerto}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print(f"\n🛑 Servidor detenido")
                server.shutdown()

        define('servidor_iniciar', servidor_iniciar)
        define('server_start', servidor_iniciar)
        define('iniciar_servidor', servidor_iniciar)
        define('start_server', servidor_iniciar)
        define('escuchar', servidor_iniciar)
        define('listen', servidor_iniciar)

        def servidor_iniciar_async(puerto=8080, host='0.0.0.0'):
            puerto = int(puerto)
            host = str(host)
            server = HTTPServer((host, puerto), MesaHandler)
            _servers[puerto] = server
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            print(f"🌐 Servidor Mesa en http://{host}:{puerto} (async)")
            return {'puerto': puerto, 'host': host}

        define('servidor_iniciar_async', servidor_iniciar_async)
        define('server_start_async', servidor_iniciar_async)

        def servidor_detener(puerto=8080):
            puerto = int(puerto)
            if puerto in _servers:
                _servers[puerto].shutdown()
                del _servers[puerto]
                return True
            return False

        define('servidor_detener', servidor_detener)
        define('server_stop', servidor_detener)
        define('detener_servidor', servidor_detener)
        define('stop_server', servidor_detener)


# ============================================================
# JSON NATIVO
# ============================================================

class MesaJSON:

    @staticmethod
    def _mesa_to_python(obj):
        if obj is None:
            return None
        if isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, list):
            return [MesaJSON._mesa_to_python(x) for x in obj]
        if isinstance(obj, dict):
            return {str(k): MesaJSON._mesa_to_python(v) for k, v in obj.items()}
        if isinstance(obj, tuple):
            return [MesaJSON._mesa_to_python(x) for x in obj]
        if hasattr(obj, 'fields') and hasattr(obj, 'shape'):
            return {k: MesaJSON._mesa_to_python(v) for k, v in obj.fields.items()}
        if hasattr(obj, 'is_ok') and hasattr(obj, 'value'):
            if obj.is_ok:
                return {'ok': True, 'value': MesaJSON._mesa_to_python(obj.value)}
            else:
                return {'ok': False, 'error': MesaJSON._mesa_to_python(obj.error)}
        return str(obj)

    @staticmethod
    def _python_to_mesa(obj):
        if obj is None:
            return None
        if isinstance(obj, bool):
            return obj
        if isinstance(obj, int):
            return obj
        if isinstance(obj, float):
            if obj == int(obj) and not (obj == float('inf') or obj == float('-inf')):
                return int(obj)
            return obj
        if isinstance(obj, str):
            return obj
        if isinstance(obj, list):
            return [MesaJSON._python_to_mesa(x) for x in obj]
        if isinstance(obj, dict):
            return {k: MesaJSON._python_to_mesa(v) for k, v in obj.items()}
        return obj

    @staticmethod
    def register(env, define, interpreter):

        def json_parsear(texto):
            try:
                return MesaJSON._python_to_mesa(json.loads(str(texto)))
            except json.JSONDecodeError as e:
                raise MesaRuntimeError(f"JSON invalido: {e.msg} (linea {e.lineno})")
            except Exception as e:
                raise MesaRuntimeError(f"Error JSON: {e}")

        define('json_parsear', json_parsear)
        define('json_parse', json_parsear)
        define('de_json', json_parsear)
        define('from_json', json_parsear)

        def json_texto(obj, indent=None):
            try:
                p = MesaJSON._mesa_to_python(obj)
                if indent is not None:
                    return json.dumps(p, indent=int(indent), ensure_ascii=False)
                return json.dumps(p, ensure_ascii=False)
            except Exception as e:
                raise MesaRuntimeError(f"Error JSON: {e}")

        define('json_texto', json_texto)
        define('json_string', json_texto)
        define('a_json', json_texto)
        define('to_json', json_texto)

        def json_bonito(obj, indent=2):
            try:
                p = MesaJSON._mesa_to_python(obj)
                return json.dumps(p, indent=int(indent), ensure_ascii=False)
            except Exception as e:
                raise MesaRuntimeError(f"Error JSON: {e}")

        define('json_bonito', json_bonito)
        define('json_pretty', json_bonito)

        def json_leer_archivo(path, encoding='utf-8'):
            try:
                with open(str(path), 'r', encoding=encoding) as f:
                    return MesaJSON._python_to_mesa(json.load(f))
            except FileNotFoundError:
                raise MesaRuntimeError(f"Archivo no encontrado: '{path}'")
            except json.JSONDecodeError as e:
                raise MesaRuntimeError(f"JSON invalido en '{path}': {e.msg}")
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('json_leer_archivo', json_leer_archivo)
        define('json_read_file', json_leer_archivo)
        define('leer_json', json_leer_archivo)
        define('read_json', json_leer_archivo)

        def json_escribir_archivo(path, obj, indent=2, encoding='utf-8'):
            try:
                dir_path = os.path.dirname(str(path))
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                p = MesaJSON._mesa_to_python(obj)
                with open(str(path), 'w', encoding=encoding) as f:
                    json.dump(p, f, indent=int(indent), ensure_ascii=False)
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('json_escribir_archivo', json_escribir_archivo)
        define('json_write_file', json_escribir_archivo)
        define('escribir_json', json_escribir_archivo)
        define('write_json', json_escribir_archivo)
        define('guardar_json', json_escribir_archivo)
        define('save_json', json_escribir_archivo)

        def json_valido(texto):
            try:
                json.loads(str(texto))
                return True
            except:
                return False

        define('json_valido', json_valido)
        define('json_valid', json_valido)
        define('es_json', json_valido)
        define('is_json', json_valido)

        def json_obtener(obj, ruta, default=None):
            try:
                keys = str(ruta).split('.')
                current = obj
                for key in keys:
                    if isinstance(current, dict):
                        if key in current:
                            current = current[key]
                        else:
                            return default
                    elif isinstance(current, list):
                        try:
                            current = current[int(key)]
                        except:
                            return default
                    elif hasattr(current, 'fields'):
                        if key in current.fields:
                            current = current.fields[key]
                        else:
                            return default
                    else:
                        return default
                return current
            except:
                return default

        define('json_obtener', json_obtener)
        define('json_get', json_obtener)
        define('json_ruta', json_obtener)
        define('json_path', json_obtener)

        def json_establecer(obj, ruta, valor):
            keys = str(ruta).split('.')
            current = obj
            for key in keys[:-1]:
                if isinstance(current, dict):
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                elif isinstance(current, list):
                    current = current[int(key)]
            last = keys[-1]
            if isinstance(current, dict):
                current[last] = valor
            elif isinstance(current, list):
                current[int(last)] = valor
            return obj

        define('json_establecer', json_establecer)
        define('json_set', json_establecer)

        def json_merge(base, *others):
            if not isinstance(base, dict):
                raise MesaRuntimeError("json_merge requiere diccionarios")
            result = dict(base)
            for other in others:
                if isinstance(other, dict):
                    result.update(other)
            return result

        define('json_merge', json_merge)
        define('json_combinar', json_merge)
        define('merge', json_merge)

        def json_claves(obj):
            if isinstance(obj, dict):
                return list(obj.keys())
            raise MesaRuntimeError("Se requiere diccionario")

        def json_valores(obj):
            if isinstance(obj, dict):
                return list(obj.values())
            raise MesaRuntimeError("Se requiere diccionario")

        define('json_claves', json_claves)
        define('json_keys', json_claves)
        define('json_valores', json_valores)
        define('json_values', json_valores)

        def json_filtrar(obj, claves):
            if isinstance(obj, dict) and isinstance(claves, list):
                return {k: v for k, v in obj.items() if k in claves}
            raise MesaRuntimeError("Se requiere objeto y lista")

        define('json_filtrar', json_filtrar)
        define('json_filter', json_filtrar)

        def json_aplanar(obj, prefix='', sep='.'):
            result = {}
            def _flat(cur, pre):
                if isinstance(cur, dict):
                    for k, v in cur.items():
                        _flat(v, f"{pre}{sep}{k}" if pre else k)
                elif isinstance(cur, list):
                    for i, v in enumerate(cur):
                        _flat(v, f"{pre}{sep}{i}" if pre else str(i))
                else:
                    result[pre] = cur
            _flat(obj, prefix)
            return result

        define('json_aplanar', json_aplanar)
        define('json_flatten', json_aplanar)

        def crear_mapa(*args):
            result = {}
            i = 0
            while i < len(args) - 1:
                result[str(args[i])] = args[i + 1]
                i += 2
            return result

        define('crear_mapa', crear_mapa)
        define('create_map', crear_mapa)
        define('mapa', crear_mapa)
        define('objeto', crear_mapa)
        define('object', crear_mapa)


# ============================================================
# REGEX - Expresiones Regulares
# ============================================================

class MesaRegex:

    @staticmethod
    def register(env, define, interpreter):

        def regex_buscar(patron, texto):
            try:
                m = re.search(str(patron), str(texto))
                if m:
                    return {
                        'encontrado': True, 'found': True,
                        'valor': m.group(), 'value': m.group(),
                        'inicio': m.start(), 'start': m.start(),
                        'fin': m.end(), 'end': m.end(),
                        'grupos': list(m.groups()), 'groups': list(m.groups()),
                    }
                return {'encontrado': False, 'found': False, 'valor': None, 'value': None}
            except re.error as e:
                raise MesaRuntimeError(f"Regex invalido: {e}")

        define('regex_buscar', regex_buscar)
        define('regex_search', regex_buscar)
        define('regex_encontrar', regex_buscar)
        define('regex_find', regex_buscar)

        def regex_coincidir(patron, texto):
            try:
                m = re.match(str(patron), str(texto))
                if m:
                    return {
                        'encontrado': True, 'found': True,
                        'valor': m.group(), 'value': m.group(),
                        'grupos': list(m.groups()), 'groups': list(m.groups()),
                    }
                return {'encontrado': False, 'found': False}
            except re.error as e:
                raise MesaRuntimeError(f"Regex invalido: {e}")

        define('regex_coincidir', regex_coincidir)
        define('regex_match', regex_coincidir)

        def regex_todos(patron, texto):
            try:
                return re.findall(str(patron), str(texto))
            except re.error as e:
                raise MesaRuntimeError(f"Regex invalido: {e}")

        define('regex_todos', regex_todos)
        define('regex_all', regex_todos)
        define('regex_findall', regex_todos)
        define('regex_buscar_todos', regex_todos)

        def regex_reemplazar(patron, reemplazo, texto, max_reemplazos=0):
            try:
                return re.sub(str(patron), str(reemplazo), str(texto), count=int(max_reemplazos))
            except re.error as e:
                raise MesaRuntimeError(f"Regex invalido: {e}")

        define('regex_reemplazar', regex_reemplazar)
        define('regex_replace', regex_reemplazar)
        define('regex_sub', regex_reemplazar)

        def regex_dividir(patron, texto, max_divisiones=0):
            try:
                return re.split(str(patron), str(texto), maxsplit=int(max_divisiones))
            except re.error as e:
                raise MesaRuntimeError(f"Regex invalido: {e}")

        define('regex_dividir', regex_dividir)
        define('regex_split', regex_dividir)

        def regex_test(patron, texto):
            try:
                return bool(re.search(str(patron), str(texto)))
            except re.error as e:
                raise MesaRuntimeError(f"Regex invalido: {e}")

        define('regex_test', regex_test)
        define('regex_probar', regex_test)
        define('regex_es', regex_test)

        def regex_escapar(texto):
            return re.escape(str(texto))

        define('regex_escapar', regex_escapar)
        define('regex_escape', regex_escapar)

        def es_email(texto):
            return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(texto)))

        def es_url(texto):
            return bool(re.match(r'^https?://[^\s/$.?#].[^\s]*$', str(texto)))

        def es_numero_texto(texto):
            return bool(re.match(r'^-?\d+(\.\d+)?$', str(texto)))

        def es_alfanumerico(texto):
            return bool(re.match(r'^[a-zA-Z0-9]+$', str(texto)))

        define('es_email', es_email)
        define('is_email', es_email)
        define('es_url', es_url)
        define('is_url', es_url)
        define('es_numero_texto', es_numero_texto)
        define('is_numeric', es_numero_texto)
        define('es_alfanumerico', es_alfanumerico)
        define('is_alphanumeric', es_alfanumerico)


# ============================================================
# CRYPTO - Criptografia y Hashing
# ============================================================

class MesaCrypto:

    @staticmethod
    def register(env, define, interpreter):

        def hash_md5(texto):
            return hashlib.md5(str(texto).encode('utf-8')).hexdigest()

        def hash_sha1(texto):
            return hashlib.sha1(str(texto).encode('utf-8')).hexdigest()

        def hash_sha256(texto):
            return hashlib.sha256(str(texto).encode('utf-8')).hexdigest()

        def hash_sha512(texto):
            return hashlib.sha512(str(texto).encode('utf-8')).hexdigest()

        define('hash_md5', hash_md5)
        define('md5', hash_md5)
        define('hash_sha1', hash_sha1)
        define('sha1', hash_sha1)
        define('hash_sha256', hash_sha256)
        define('sha256', hash_sha256)
        define('hash_sha512', hash_sha512)
        define('sha512', hash_sha512)

        def hash_hmac(clave, mensaje, algo='sha256'):
            algos = {'md5': hashlib.md5, 'sha1': hashlib.sha1, 'sha256': hashlib.sha256, 'sha512': hashlib.sha512}
            h = algos.get(str(algo), hashlib.sha256)
            return hmac.new(str(clave).encode('utf-8'), str(mensaje).encode('utf-8'), h).hexdigest()

        define('hash_hmac', hash_hmac)
        define('hmac', hash_hmac)

        def hash_archivo(path, algo='sha256'):
            algos = {'md5': hashlib.md5, 'sha1': hashlib.sha1, 'sha256': hashlib.sha256, 'sha512': hashlib.sha512}
            h = algos.get(str(algo), hashlib.sha256)()
            try:
                with open(str(path), 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        h.update(chunk)
                return h.hexdigest()
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('hash_archivo', hash_archivo)
        define('hash_file', hash_archivo)

        def base64_codificar(texto):
            if isinstance(texto, list):
                return base64.b64encode(bytes(texto)).decode('utf-8')
            return base64.b64encode(str(texto).encode('utf-8')).decode('utf-8')

        def base64_decodificar(texto):
            try:
                return base64.b64decode(str(texto)).decode('utf-8')
            except:
                return list(base64.b64decode(str(texto)))

        define('base64_codificar', base64_codificar)
        define('base64_encode', base64_codificar)
        define('base64_decodificar', base64_decodificar)
        define('base64_decode', base64_decodificar)

        def generar_uuid():
            return str(uuid.uuid4())

        define('generar_uuid', generar_uuid)
        define('uuid', generar_uuid)
        define('generate_uuid', generar_uuid)

        def generar_token(longitud=32):
            chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            return ''.join(random.choice(chars) for _ in range(int(longitud)))

        define('generar_token', generar_token)
        define('generate_token', generar_token)
        define('token_aleatorio', generar_token)
        define('random_token', generar_token)

        def generar_bytes_aleatorios(n=16):
            return list(os.urandom(int(n)))

        define('generar_bytes_aleatorios', generar_bytes_aleatorios)
        define('random_bytes', generar_bytes_aleatorios)

        def hex_codificar(data):
            if isinstance(data, list):
                return bytes(data).hex()
            return str(data).encode('utf-8').hex()

        def hex_decodificar(texto):
            try:
                return bytes.fromhex(str(texto)).decode('utf-8')
            except:
                return list(bytes.fromhex(str(texto)))

        define('hex_codificar', hex_codificar)
        define('hex_encode', hex_codificar)
        define('hex_decodificar', hex_decodificar)
        define('hex_decode', hex_decodificar)

        def hash_password(password, salt=None):
            if salt is None:
                salt = os.urandom(16).hex()
            else:
                salt = str(salt)
            h = hashlib.pbkdf2_hmac('sha256', str(password).encode('utf-8'), salt.encode('utf-8'), 100000)
            return {'hash': h.hex(), 'salt': salt}

        def verificar_password(password, hash_val, salt):
            h = hashlib.pbkdf2_hmac('sha256', str(password).encode('utf-8'), str(salt).encode('utf-8'), 100000)
            return h.hex() == str(hash_val)

        define('hash_password', hash_password)
        define('hash_contraseña', hash_password)
        define('verificar_password', verificar_password)
        define('verify_password', verificar_password)
        define('verificar_contraseña', verificar_password)


# ============================================================
# DATABASE - SQLite integrado
# ============================================================

class MesaDatabase:

    @staticmethod
    def register(env, define, interpreter):

        _connections = {}

        def db_conectar(path=':memory:'):
            try:
                conn = sqlite3.connect(str(path))
                conn.row_factory = sqlite3.Row
                conn_id = f"db_{id(conn)}"
                _connections[conn_id] = conn
                return conn_id
            except Exception as e:
                raise MesaRuntimeError(f"Error BD: {e}")

        define('db_conectar', db_conectar)
        define('db_connect', db_conectar)
        define('conectar_bd', db_conectar)
        define('connect_db', db_conectar)

        def _get_conn(conn_id):
            conn = _connections.get(str(conn_id))
            if conn is None:
                raise MesaRuntimeError(f"Conexion no encontrada: {conn_id}")
            return conn

        def db_ejecutar(conn_id, sql, params=None):
            try:
                conn = _get_conn(conn_id)
                if params is None:
                    params = []
                if isinstance(params, list):
                    cursor = conn.execute(str(sql), params)
                else:
                    cursor = conn.execute(str(sql), params)
                conn.commit()
                return {'filas_afectadas': cursor.rowcount, 'rows_affected': cursor.rowcount, 'ultimo_id': cursor.lastrowid, 'last_id': cursor.lastrowid}
            except Exception as e:
                raise MesaRuntimeError(f"Error SQL: {e}")

        define('db_ejecutar', db_ejecutar)
        define('db_execute', db_ejecutar)
        define('db_exec', db_ejecutar)

        def db_consultar(conn_id, sql, params=None):
            try:
                conn = _get_conn(conn_id)
                if params is None:
                    params = []
                cursor = conn.execute(str(sql), params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    d = {}
                    for i, col in enumerate(columns):
                        d[col] = row[i]
                    result.append(d)
                return result
            except Exception as e:
                raise MesaRuntimeError(f"Error SQL: {e}")

        define('db_consultar', db_consultar)
        define('db_query', db_consultar)
        define('db_buscar', db_consultar)

        def db_consultar_uno(conn_id, sql, params=None):
            rows = db_consultar(conn_id, sql, params)
            if rows:
                return rows[0]
            return None

        define('db_consultar_uno', db_consultar_uno)
        define('db_query_one', db_consultar_uno)
        define('db_uno', db_consultar_uno)

        def db_insertar(conn_id, tabla, datos):
            if not isinstance(datos, dict):
                raise MesaRuntimeError("db_insertar requiere un diccionario")
            cols = list(datos.keys())
            vals = list(datos.values())
            placeholders = ', '.join(['?' for _ in cols])
            col_names = ', '.join(cols)
            sql = f"INSERT INTO {tabla} ({col_names}) VALUES ({placeholders})"
            return db_ejecutar(conn_id, sql, vals)

        define('db_insertar', db_insertar)
        define('db_insert', db_insertar)

        def db_actualizar(conn_id, tabla, datos, where, where_params=None):
            if not isinstance(datos, dict):
                raise MesaRuntimeError("db_actualizar requiere un diccionario")
            sets = ', '.join([f"{k} = ?" for k in datos.keys()])
            vals = list(datos.values())
            if where_params:
                if isinstance(where_params, list):
                    vals.extend(where_params)
                else:
                    vals.append(where_params)
            sql = f"UPDATE {tabla} SET {sets} WHERE {where}"
            return db_ejecutar(conn_id, sql, vals)

        define('db_actualizar', db_actualizar)
        define('db_update', db_actualizar)

        def db_eliminar(conn_id, tabla, where, params=None):
            if params is None:
                params = []
            sql = f"DELETE FROM {tabla} WHERE {where}"
            return db_ejecutar(conn_id, sql, params)

        define('db_eliminar', db_eliminar)
        define('db_delete', db_eliminar)

        def db_tablas(conn_id):
            rows = db_consultar(conn_id, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [r['name'] for r in rows]

        define('db_tablas', db_tablas)
        define('db_tables', db_tablas)

        def db_columnas(conn_id, tabla):
            rows = db_consultar(conn_id, f"PRAGMA table_info({tabla})")
            return [{'nombre': r['name'], 'tipo': r['type'], 'no_nulo': bool(r['notnull']), 'default': r['dflt_value']} for r in rows]

        define('db_columnas', db_columnas)
        define('db_columns', db_columnas)

        def db_contar(conn_id, tabla, where=None, params=None):
            sql = f"SELECT COUNT(*) as count FROM {tabla}"
            if where:
                sql += f" WHERE {where}"
            row = db_consultar_uno(conn_id, sql, params or [])
            return row['count'] if row else 0

        define('db_contar', db_contar)
        define('db_count', db_contar)

        def db_cerrar(conn_id):
            conn = _connections.get(str(conn_id))
            if conn:
                conn.close()
                del _connections[str(conn_id)]
                return True
            return False

        define('db_cerrar', db_cerrar)
        define('db_close', db_cerrar)
        define('cerrar_bd', db_cerrar)

        def db_transaccion(conn_id, func):
            conn = _get_conn(conn_id)
            try:
                if isinstance(func, MesaFunc):
                    result = interpreter._call_func(func, [conn_id])
                elif callable(func):
                    result = func(conn_id)
                else:
                    raise MesaRuntimeError("Se requiere funcion")
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                raise MesaRuntimeError(f"Transaccion fallida: {e}")

        define('db_transaccion', db_transaccion)
        define('db_transaction', db_transaccion)


# ============================================================
# CONCURRENCIA - Hilos y Tareas
# ============================================================

class MesaConcurrency:

    @staticmethod
    def register(env, define, interpreter):

        _channels = {}

        def tarea_crear(func, *args):
            result_holder = {'value': None, 'error': None, 'done': False}

            def _run():
                try:
                    if isinstance(func, MesaFunc):
                        result_holder['value'] = interpreter._call_func(func, list(args))
                    elif callable(func):
                        result_holder['value'] = func(*args)
                except Exception as e:
                    result_holder['error'] = str(e)
                finally:
                    result_holder['done'] = True

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            result_holder['_thread'] = t
            return result_holder

        define('tarea_crear', tarea_crear)
        define('task_create', tarea_crear)
        define('crear_tarea', tarea_crear)
        define('create_task', tarea_crear)
        define('hilo', tarea_crear)
        define('thread', tarea_crear)

        def tarea_esperar(tarea, timeout=None):
            t = tarea.get('_thread')
            if t:
                if timeout is not None:
                    t.join(float(timeout))
                else:
                    t.join()
            if tarea.get('error'):
                raise MesaRuntimeError(f"Error en tarea: {tarea['error']}")
            return tarea.get('value')

        define('tarea_esperar', tarea_esperar)
        define('task_wait', tarea_esperar)
        define('esperar_tarea', tarea_esperar)
        define('await_task', tarea_esperar)

        def tarea_lista(tarea):
            return tarea.get('done', False)

        define('tarea_lista', tarea_lista)
        define('task_done', tarea_lista)
        define('tarea_terminada', tarea_lista)

        def tareas_esperar_todas(*tareas):
            flat = []
            for t in tareas:
                if isinstance(t, list):
                    flat.extend(t)
                else:
                    flat.append(t)
            results = []
            for t in flat:
                results.append(tarea_esperar(t))
            return results

        define('tareas_esperar_todas', tareas_esperar_todas)
        define('tasks_wait_all', tareas_esperar_todas)
        define('esperar_todas', tareas_esperar_todas)
        define('await_all', tareas_esperar_todas)

        def paralelo(*funcs):
            tareas = []
            for f in funcs:
                tareas.append(tarea_crear(f))
            return tareas_esperar_todas(tareas)

        define('paralelo', paralelo)
        define('parallel', paralelo)

        def canal_crear(max_size=0):
            q = queue.Queue(maxsize=int(max_size))
            canal_id = f"ch_{id(q)}"
            _channels[canal_id] = q
            return canal_id

        define('canal_crear', canal_crear)
        define('channel_create', canal_crear)
        define('crear_canal', canal_crear)
        define('create_channel', canal_crear)

        def canal_enviar(canal_id, valor, timeout=None):
            q = _channels.get(str(canal_id))
            if q is None:
                raise MesaRuntimeError(f"Canal no encontrado: {canal_id}")
            try:
                if timeout is not None:
                    q.put(valor, timeout=float(timeout))
                else:
                    q.put(valor)
                return True
            except queue.Full:
                raise MesaRuntimeError("Canal lleno")

        define('canal_enviar', canal_enviar)
        define('channel_send', canal_enviar)
        define('enviar', canal_enviar)
        define('send', canal_enviar)

        def canal_recibir(canal_id, timeout=None):
            q = _channels.get(str(canal_id))
            if q is None:
                raise MesaRuntimeError(f"Canal no encontrado: {canal_id}")
            try:
                if timeout is not None:
                    return q.get(timeout=float(timeout))
                else:
                    return q.get()
            except queue.Empty:
                raise MesaRuntimeError("Canal vacio (timeout)")

        define('canal_recibir', canal_recibir)
        define('channel_receive', canal_recibir)
        define('recibir', canal_recibir)
        define('receive', canal_recibir)

        def canal_vacio(canal_id):
            q = _channels.get(str(canal_id))
            if q is None:
                raise MesaRuntimeError(f"Canal no encontrado: {canal_id}")
            return q.empty()

        define('canal_vacio', canal_vacio)
        define('channel_empty', canal_vacio)

        def canal_tamanio(canal_id):
            q = _channels.get(str(canal_id))
            if q is None:
                raise MesaRuntimeError(f"Canal no encontrado: {canal_id}")
            return q.qsize()

        define('canal_tamaño', canal_tamanio)
        define('canal_tamanio', canal_tamanio)
        define('channel_size', canal_tamanio)

        def mutex_crear():
            lock = threading.Lock()
            return {'_lock': lock, 'locked': False}

        def mutex_bloquear(m):
            m['_lock'].acquire()
            m['locked'] = True
            return True

        def mutex_desbloquear(m):
            m['_lock'].release()
            m['locked'] = False
            return True

        define('mutex_crear', mutex_crear)
        define('mutex_create', mutex_crear)
        define('crear_mutex', mutex_crear)
        define('mutex_bloquear', mutex_bloquear)
        define('mutex_lock', mutex_bloquear)
        define('bloquear', mutex_bloquear)
        define('lock', mutex_bloquear)
        define('mutex_desbloquear', mutex_desbloquear)
        define('mutex_unlock', mutex_desbloquear)
        define('desbloquear', mutex_desbloquear)
        define('unlock', mutex_desbloquear)

        def atomico(func, *args):
            lock = threading.Lock()
            with lock:
                if isinstance(func, MesaFunc):
                    return interpreter._call_func(func, list(args))
                elif callable(func):
                    return func(*args)

        define('atomico', atomico)
        define('atomic', atomico)

        def dormir_ms(ms):
            time.sleep(float(ms) / 1000.0)

        define('dormir_ms', dormir_ms)
        define('sleep_ms', dormir_ms)

        def temporizador(segundos, func, *args):
            def _run():
                time.sleep(float(segundos))
                if isinstance(func, MesaFunc):
                    interpreter._call_func(func, list(args))
                elif callable(func):
                    func(*args)
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return True

        define('temporizador', temporizador)
        define('timer', temporizador)
        define('set_timeout', temporizador)

        def intervalo(segundos, func, veces=None, *args):
            state = {'running': True, 'count': 0}

            def _run():
                max_times = int(veces) if veces is not None else None
                while state['running']:
                    time.sleep(float(segundos))
                    if not state['running']:
                        break
                    if isinstance(func, MesaFunc):
                        interpreter._call_func(func, list(args))
                    elif callable(func):
                        func(*args)
                    state['count'] += 1
                    if max_times and state['count'] >= max_times:
                        break

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return state

        def intervalo_detener(state):
            state['running'] = False
            return True

        define('intervalo', intervalo)
        define('interval', intervalo)
        define('set_interval', intervalo)
        define('intervalo_detener', intervalo_detener)
        define('clear_interval', intervalo_detener)


# ============================================================
# CSV
# ============================================================

class MesaCSV:

    @staticmethod
    def register(env, define, interpreter):

        def csv_leer(path, delimitador=',', encoding='utf-8'):
            try:
                with open(str(path), 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f, delimiter=str(delimitador))
                    return [dict(row) for row in reader]
            except Exception as e:
                raise MesaRuntimeError(f"Error CSV: {e}")

        define('csv_leer', csv_leer)
        define('csv_read', csv_leer)
        define('leer_csv', csv_leer)
        define('read_csv', csv_leer)

        def csv_escribir(path, datos, columnas=None, delimitador=',', encoding='utf-8'):
            try:
                if not datos:
                    return False
                if columnas is None:
                    if isinstance(datos[0], dict):
                        columnas = list(datos[0].keys())
                    else:
                        raise MesaRuntimeError("Se requieren columnas")
                dir_path = os.path.dirname(str(path))
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                with open(str(path), 'w', encoding=encoding, newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=columnas, delimiter=str(delimitador))
                    writer.writeheader()
                    for row in datos:
                        if isinstance(row, dict):
                            writer.writerow(row)
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error CSV: {e}")

        define('csv_escribir', csv_escribir)
        define('csv_write', csv_escribir)
        define('escribir_csv', csv_escribir)
        define('write_csv', csv_escribir)

        def csv_parsear(texto, delimitador=','):
            try:
                reader = csv.DictReader(io.StringIO(str(texto)), delimiter=str(delimitador))
                return [dict(row) for row in reader]
            except Exception as e:
                raise MesaRuntimeError(f"Error CSV: {e}")

        define('csv_parsear', csv_parsear)
        define('csv_parse', csv_parsear)

        def csv_texto(datos, columnas=None, delimitador=','):
            try:
                if not datos:
                    return ''
                if columnas is None and isinstance(datos[0], dict):
                    columnas = list(datos[0].keys())
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=columnas, delimiter=str(delimitador))
                writer.writeheader()
                for row in datos:
                    if isinstance(row, dict):
                        writer.writerow(row)
                return output.getvalue()
            except Exception as e:
                raise MesaRuntimeError(f"Error CSV: {e}")

        define('csv_texto', csv_texto)
        define('csv_string', csv_texto)
        define('a_csv', csv_texto)
        define('to_csv', csv_texto)


# ============================================================
# COMPRESION
# ============================================================

class MesaCompression:

    @staticmethod
    def register(env, define, interpreter):

        def comprimir(data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif isinstance(data, list):
                data = bytes(data)
            return list(zlib.compress(data))

        def descomprimir(data):
            if isinstance(data, list):
                data = bytes(data)
            try:
                return zlib.decompress(data).decode('utf-8')
            except:
                return list(zlib.decompress(data))

        define('comprimir', comprimir)
        define('compress', comprimir)
        define('descomprimir', descomprimir)
        define('decompress', descomprimir)

        def gzip_comprimir(data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif isinstance(data, list):
                data = bytes(data)
            return list(gzip.compress(data))

        def gzip_descomprimir(data):
            if isinstance(data, list):
                data = bytes(data)
            try:
                return gzip.decompress(data).decode('utf-8')
            except:
                return list(gzip.decompress(data))

        define('gzip_comprimir', gzip_comprimir)
        define('gzip_compress', gzip_comprimir)
        define('gzip_descomprimir', gzip_descomprimir)
        define('gzip_decompress', gzip_descomprimir)

        def comprimir_archivo(origen, destino=None):
            if destino is None:
                destino = str(origen) + '.gz'
            try:
                with open(str(origen), 'rb') as f_in:
                    with gzip.open(str(destino), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        def descomprimir_archivo(origen, destino=None):
            if destino is None:
                destino = str(origen).replace('.gz', '')
            try:
                with gzip.open(str(origen), 'rb') as f_in:
                    with open(str(destino), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                return True
            except Exception as e:
                raise MesaRuntimeError(f"Error: {e}")

        define('comprimir_archivo', comprimir_archivo)
        define('compress_file', comprimir_archivo)
        define('descomprimir_archivo', descomprimir_archivo)
        define('decompress_file', descomprimir_archivo)


# ============================================================
# DATETIME
# ============================================================

class MesaDateTime:

    @staticmethod
    def register(env, define, interpreter):

        def ahora():
            return datetime.datetime.now().isoformat()

        def ahora_utc():
            return datetime.datetime.utcnow().isoformat()

        def timestamp():
            return time.time()

        def fecha_formato(formato=None, ts=None):
            if ts is not None:
                dt = datetime.datetime.fromtimestamp(float(ts))
            else:
                dt = datetime.datetime.now()
            if formato is None:
                formato = '%Y-%m-%d %H:%M:%S'
            return dt.strftime(str(formato))

        define('ahora', ahora)
        define('now', ahora)
        define('ahora_utc', ahora_utc)
        define('now_utc', ahora_utc)
        define('timestamp', timestamp)
        define('marca_tiempo', timestamp)
        define('fecha_formato', fecha_formato)
        define('date_format', fecha_formato)
        define('formatear_fecha', fecha_formato)

        def fecha_parsear(texto, formato='%Y-%m-%d'):
            try:
                dt = datetime.datetime.strptime(str(texto), str(formato))
                return {'año': dt.year, 'mes': dt.month, 'dia': dt.day, 'hora': dt.hour, 'minuto': dt.minute, 'segundo': dt.second, 'timestamp': dt.timestamp(), 'iso': dt.isoformat()}
            except Exception as e:
                raise MesaRuntimeError(f"Error fecha: {e}")

        define('fecha_parsear', fecha_parsear)
        define('date_parse', fecha_parsear)
        define('parsear_fecha', fecha_parsear)

        def fecha_diferencia(fecha1, fecha2):
            try:
                if isinstance(fecha1, str):
                    dt1 = datetime.datetime.fromisoformat(fecha1)
                else:
                    dt1 = datetime.datetime.fromtimestamp(float(fecha1))
                if isinstance(fecha2, str):
                    dt2 = datetime.datetime.fromisoformat(fecha2)
                else:
                    dt2 = datetime.datetime.fromtimestamp(float(fecha2))
                diff = abs(dt2 - dt1)
                return {'dias': diff.days, 'segundos': diff.total_seconds(), 'horas': diff.total_seconds() / 3600, 'minutos': diff.total_seconds() / 60}
            except Exception as e:
                raise MesaRuntimeError(f"Error fecha: {e}")

        define('fecha_diferencia', fecha_diferencia)
        define('date_diff', fecha_diferencia)

        def fecha_sumar(fecha=None, dias=0, horas=0, minutos=0, segundos=0):
            try:
                if fecha is None:
                    dt = datetime.datetime.now()
                elif isinstance(fecha, str):
                    dt = datetime.datetime.fromisoformat(fecha)
                else:
                    dt = datetime.datetime.fromtimestamp(float(fecha))
                delta = datetime.timedelta(days=int(dias), hours=int(horas), minutes=int(minutos), seconds=int(segundos))
                result = dt + delta
                return result.isoformat()
            except Exception as e:
                raise MesaRuntimeError(f"Error fecha: {e}")

        define('fecha_sumar', fecha_sumar)
        define('date_add', fecha_sumar)

        def dia_semana(fecha=None):
            try:
                if fecha is None:
                    dt = datetime.datetime.now()
                elif isinstance(fecha, str):
                    dt = datetime.datetime.fromisoformat(fecha)
                else:
                    dt = datetime.datetime.fromtimestamp(float(fecha))
                dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
                return dias[dt.weekday()]
            except Exception as e:
                raise MesaRuntimeError(f"Error fecha: {e}")

        define('dia_semana', dia_semana)
        define('day_of_week', dia_semana)
        define('weekday', dia_semana)


# ============================================================
# SISTEMA / PROCESOS
# ============================================================

class MesaSystem:

    @staticmethod
    def register(env, define, interpreter):

        def ejecutar_comando(cmd, timeout=30):
            try:
                result = subprocess.run(str(cmd), shell=True, capture_output=True, text=True, timeout=int(timeout))
                return {'salida': result.stdout, 'output': result.stdout, 'error': result.stderr, 'codigo': result.returncode, 'code': result.returncode, 'ok': result.returncode == 0}
            except subprocess.TimeoutExpired:
                raise MesaRuntimeError(f"Comando timeout: {cmd}")
            except Exception as e:
                raise MesaRuntimeError(f"Error comando: {e}")

        define('ejecutar_comando', ejecutar_comando)
        define('exec_command', ejecutar_comando)
        define('shell', ejecutar_comando)
        define('comando', ejecutar_comando)
        define('command', ejecutar_comando)
        define('cmd', ejecutar_comando)

        def var_entorno(nombre, default=None):
            return os.environ.get(str(nombre), default)

        def set_var_entorno(nombre, valor):
            os.environ[str(nombre)] = str(valor)
            return True

        define('var_entorno', var_entorno)
        define('env_var', var_entorno)
        define('entorno', var_entorno)
        define('getenv', var_entorno)
        define('set_var_entorno', set_var_entorno)
        define('setenv', set_var_entorno)

        def argumentos():
            return sys.argv[:]

        define('argumentos', argumentos)
        define('args', argumentos)
        define('sys_args', argumentos)

        def plataforma():
            return sys.platform

        define('plataforma', plataforma)
        define('platform', plataforma)

        def info_sistema():
            return {'plataforma': sys.platform, 'python': sys.version, 'mesa': '2.2.0', 'pid': os.getpid(), 'cwd': os.getcwd(), 'usuario': os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))}

        define('info_sistema', info_sistema)
        define('system_info', info_sistema)

        def medir_tiempo(func, *args):
            start = time.perf_counter()
            if isinstance(func, MesaFunc):
                result = interpreter._call_func(func, list(args))
            elif callable(func):
                result = func(*args)
            else:
                result = None
            elapsed = time.perf_counter() - start
            return {'resultado': result, 'result': result, 'tiempo': elapsed, 'time': elapsed, 'ms': elapsed * 1000}

        define('medir_tiempo', medir_tiempo)
        define('measure_time', medir_tiempo)
        define('benchmark', medir_tiempo)
        define('cronometro', medir_tiempo)
# ============================================================
# WEB BUILDER - Crear webs sin HTML
# ============================================================

class MesaWebBuilder:
    """Sistema para crear webs sin saber HTML"""

    @staticmethod
    def register(env, define, interpreter):

        # Estado global de la página actual
        _page_state = {
            'titulo': 'Mesa Web',
            'tema': 'claro',
            'fuente': 'Arial',
            'elementos': [],
            'estilos_extra': '',
            'scripts_extra': '',
        }

        # Temas predefinidos
        _temas = {
            'claro': {
                'fondo': '#ffffff',
                'texto': '#333333',
                'primario': '#3498db',
                'secundario': '#2ecc71',
                'acento': '#e74c3c',
                'tarjeta': '#f8f9fa',
                'borde': '#dee2e6',
            },
            'oscuro': {
                'fondo': '#1a1a2e',
                'texto': '#eaeaea',
                'primario': '#0f3460',
                'secundario': '#16213e',
                'acento': '#e94560',
                'tarjeta': '#16213e',
                'borde': '#0f3460',
            },
            'naturaleza': {
                'fondo': '#f5f5dc',
                'texto': '#2d5016',
                'primario': '#228b22',
                'secundario': '#90ee90',
                'acento': '#ff6347',
                'tarjeta': '#fffef0',
                'borde': '#90ee90',
            },
            'oceano': {
                'fondo': '#e0f7fa',
                'texto': '#006064',
                'primario': '#0097a7',
                'secundario': '#4dd0e1',
                'acento': '#ff5722',
                'tarjeta': '#ffffff',
                'borde': '#b2ebf2',
            },
            'noche': {
                'fondo': '#0d1117',
                'texto': '#c9d1d9',
                'primario': '#58a6ff',
                'secundario': '#238636',
                'acento': '#f85149',
                'tarjeta': '#161b22',
                'borde': '#30363d',
            },
        }

        def _reset_page():
            _page_state['titulo'] = 'Mesa Web'
            _page_state['tema'] = 'claro'
            _page_state['fuente'] = 'Arial'
            _page_state['elementos'] = []
            _page_state['estilos_extra'] = ''
            _page_state['scripts_extra'] = ''

        def _escape_html(text):
            if text is None:
                return ''
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

        def _get_tema():
            nombre = _page_state['tema']
            return _temas.get(nombre, _temas['claro'])

        # ══════════════════════════════════════════════════
        # CONFIGURACIÓN DE PÁGINA
        # ══════════════════════════════════════════════════

        def pagina(titulo=None, tema=None, fuente=None):
            _reset_page()
            if titulo:
                _page_state['titulo'] = str(titulo)
            if tema:
                _page_state['tema'] = str(tema)
            if fuente:
                _page_state['fuente'] = str(fuente)
            return True

        define('pagina', pagina)
        define('page', pagina)
        define('web_pagina', pagina)
        define('web_page', pagina)

        def tema(nombre):
            _page_state['tema'] = str(nombre)
            return True

        define('tema', tema)
        define('theme', tema)

        # ══════════════════════════════════════════════════
        # ELEMENTOS DE CONTENIDO
        # ══════════════════════════════════════════════════

        def titulo(texto, nivel=1):
            nivel = max(1, min(6, int(nivel)))
            _page_state['elementos'].append(f'<h{nivel}>{_escape_html(texto)}</h{nivel}>')
            return True

        define('titulo', titulo)
        define('title', titulo)
        define('encabezado', titulo)
        define('heading', titulo)

        def texto(contenido, estilo=None):
            estilos = ''
            if estilo == 'negrita' or estilo == 'bold':
                estilos = 'font-weight: bold;'
            elif estilo == 'italica' or estilo == 'italic':
                estilos = 'font-style: italic;'
            elif estilo == 'subrayado' or estilo == 'underline':
                estilos = 'text-decoration: underline;'
            elif estilo == 'centro' or estilo == 'center':
                estilos = 'text-align: center;'
            style_attr = f' style="{estilos}"' if estilos else ''
            _page_state['elementos'].append(f'<p{style_attr}>{_escape_html(contenido)}</p>')
            return True

        define('texto', texto)
        define('text', texto)
        define('parrafo', texto)
        define('paragraph', texto)

        def imagen(url, alt='', ancho=None):
            estilo = ''
            if ancho:
                estilo = f' style="max-width: {ancho}px; width: 100%;"'
            _page_state['elementos'].append(f'<img src="{_escape_html(url)}" alt="{_escape_html(alt)}"{estilo}>')
            return True

        define('imagen', imagen)
        define('image', imagen)
        define('img', imagen)
        define('foto', imagen)

        def link(texto, url, nuevo_tab=False):
            target = ' target="_blank"' if nuevo_tab else ''
            _page_state['elementos'].append(f'<a href="{_escape_html(url)}"{target}>{_escape_html(texto)}</a>')
            return True

        define('link', link)
        define('enlace', link)
        define('vinculo', link)

        def boton(texto, url=None, color=None):
            tema = _get_tema()
            bg = color if color else tema['primario']
            if url:
                _page_state['elementos'].append(f'<a href="{_escape_html(url)}" class="btn" style="background:{bg};">{_escape_html(texto)}</a>')
            else:
                _page_state['elementos'].append(f'<button class="btn" style="background:{bg};">{_escape_html(texto)}</button>')
            return True

        define('boton', boton)
        define('button', boton)

        def lista(items, ordenada=False):
            tag = 'ol' if ordenada else 'ul'
            html = f'<{tag}>'
            if isinstance(items, list):
                for item in items:
                    html += f'<li>{_escape_html(item)}</li>'
            html += f'</{tag}>'
            _page_state['elementos'].append(html)
            return True

        define('lista', lista)
        define('list', lista)

        def separador():
            _page_state['elementos'].append('<hr>')
            return True

        define('separador', separador)
        define('linea', separador)
        define('hr', separador)
        define('divider', separador)

        def espacio(cantidad=1):
            _page_state['elementos'].append('<br>' * int(cantidad))
            return True

        define('espacio', espacio)
        define('space', espacio)
        define('br', espacio)

        # ══════════════════════════════════════════════════
        # CONTENEDORES
        # ══════════════════════════════════════════════════

        def tarjeta_inicio(titulo=None):
            html = '<div class="card">'
            if titulo:
                html += f'<h3>{_escape_html(titulo)}</h3>'
            _page_state['elementos'].append(html)
            return True

        def tarjeta_fin():
            _page_state['elementos'].append('</div>')
            return True

        define('tarjeta_inicio', tarjeta_inicio)
        define('card_start', tarjeta_inicio)
        define('tarjeta_fin', tarjeta_fin)
        define('card_end', tarjeta_fin)

        def tarjeta(titulo=None, contenido=None):
            html = '<div class="card">'
            if titulo:
                html += f'<h3>{_escape_html(titulo)}</h3>'
            if contenido:
                html += f'<p>{_escape_html(contenido)}</p>'
            html += '</div>'
            _page_state['elementos'].append(html)
            return True

        define('tarjeta', tarjeta)
        define('card', tarjeta)

        def seccion_inicio(titulo=None):
            html = '<section>'
            if titulo:
                html += f'<h2>{_escape_html(titulo)}</h2>'
            _page_state['elementos'].append(html)
            return True

        def seccion_fin():
            _page_state['elementos'].append('</section>')
            return True

        define('seccion_inicio', seccion_inicio)
        define('section_start', seccion_inicio)
        define('seccion_fin', seccion_fin)
        define('section_end', seccion_fin)

        def fila_inicio():
            _page_state['elementos'].append('<div class="row">')
            return True

        def fila_fin():
            _page_state['elementos'].append('</div>')
            return True

        def columna_inicio(ancho=None):
            style = ''
            if ancho:
                style = f' style="flex: 0 0 {ancho}%;"'
            _page_state['elementos'].append(f'<div class="col"{style}>')
            return True

        def columna_fin():
            _page_state['elementos'].append('</div>')
            return True

        define('fila_inicio', fila_inicio)
        define('row_start', fila_inicio)
        define('fila_fin', fila_fin)
        define('row_end', fila_fin)
        define('columna_inicio', columna_inicio)
        define('col_start', columna_inicio)
        define('columna_fin', columna_fin)
        define('col_end', columna_fin)

        # ══════════════════════════════════════════════════
        # NAVEGACIÓN
        # ══════════════════════════════════════════════════

        def navbar(titulo, links=None):
            tema = _get_tema()
            html = f'<nav style="background:{tema["primario"]}; padding:15px; margin-bottom:20px;">'
            html += f'<span style="color:white; font-size:1.5em; font-weight:bold;">{_escape_html(titulo)}</span>'
            if links and isinstance(links, list):
                html += '<span style="float:right;">'
                for item in links:
                    if isinstance(item, dict):
                        txt = item.get('texto', item.get('text', ''))
                        url = item.get('url', item.get('href', '#'))
                        html += f'<a href="{_escape_html(url)}" style="color:white; margin-left:20px; text-decoration:none;">{_escape_html(txt)}</a>'
                    elif isinstance(item, list) and len(item) >= 2:
                        html += f'<a href="{_escape_html(item[1])}" style="color:white; margin-left:20px; text-decoration:none;">{_escape_html(item[0])}</a>'
                html += '</span>'
            html += '</nav>'
            _page_state['elementos'].insert(0, html)
            return True

        define('navbar', navbar)
        define('navegacion', navbar)
        define('menu', navbar)

        def footer(texto):
            tema = _get_tema()
            html = f'<footer style="background:{tema["tarjeta"]}; padding:20px; text-align:center; margin-top:40px; border-top:1px solid {tema["borde"]};">'
            html += f'{_escape_html(texto)}'
            html += '</footer>'
            _page_state['elementos'].append(html)
            return True

        define('footer', footer)
        define('pie', footer)
        define('pie_pagina', footer)

        # ══════════════════════════════════════════════════
        # FORMULARIOS
        # ══════════════════════════════════════════════════

        def formulario_inicio(accion='#', metodo='POST'):
            _page_state['elementos'].append(f'<form action="{_escape_html(accion)}" method="{metodo}" class="form">')
            return True

        def formulario_fin():
            _page_state['elementos'].append('</form>')
            return True

        define('formulario_inicio', formulario_inicio)
        define('form_start', formulario_inicio)
        define('formulario_fin', formulario_fin)
        define('form_end', formulario_fin)

        def campo(nombre, tipo='text', etiqueta=None, placeholder='', requerido=False):
            html = '<div class="form-group">'
            if etiqueta:
                html += f'<label for="{_escape_html(nombre)}">{_escape_html(etiqueta)}</label>'
            req = ' required' if requerido else ''
            if tipo == 'textarea':
                html += f'<textarea name="{_escape_html(nombre)}" id="{_escape_html(nombre)}" placeholder="{_escape_html(placeholder)}"{req}></textarea>'
            else:
                html += f'<input type="{tipo}" name="{_escape_html(nombre)}" id="{_escape_html(nombre)}" placeholder="{_escape_html(placeholder)}"{req}>'
            html += '</div>'
            _page_state['elementos'].append(html)
            return True

        define('campo', campo)
        define('field', campo)
        define('input', campo)
        define('entrada', campo)

        def boton_enviar(texto='Enviar'):
            tema = _get_tema()
            _page_state['elementos'].append(f'<button type="submit" class="btn" style="background:{tema["primario"]};">{_escape_html(texto)}</button>')
            return True

        define('boton_enviar', boton_enviar)
        define('submit', boton_enviar)
        define('enviar', boton_enviar)

        # ══════════════════════════════════════════════════
        # TABLAS
        # ══════════════════════════════════════════════════

        def tabla(datos, columnas=None):
            if not datos:
                return True
            html = '<table class="table">'
            if columnas:
                html += '<thead><tr>'
                for col in columnas:
                    html += f'<th>{_escape_html(col)}</th>'
                html += '</tr></thead>'
            html += '<tbody>'
            for fila in datos:
                html += '<tr>'
                if isinstance(fila, dict):
                    for val in fila.values():
                        html += f'<td>{_escape_html(val)}</td>'
                elif isinstance(fila, list):
                    for val in fila:
                        html += f'<td>{_escape_html(val)}</td>'
                else:
                    html += f'<td>{_escape_html(fila)}</td>'
                html += '</tr>'
            html += '</tbody></table>'
            _page_state['elementos'].append(html)
            return True

        define('tabla', tabla)
        define('table', tabla)

        # ══════════════════════════════════════════════════
        # MULTIMEDIA
        # ══════════════════════════════════════════════════

        def video(url, ancho=None):
            estilo = f'max-width:{ancho}px;' if ancho else 'max-width:100%;'
            if 'youtube.com' in url or 'youtu.be' in url:
                video_id = ''
                if 'youtu.be/' in url:
                    video_id = url.split('youtu.be/')[-1].split('?')[0]
                elif 'v=' in url:
                    video_id = url.split('v=')[-1].split('&')[0]
                _page_state['elementos'].append(f'<iframe style="{estilo} aspect-ratio:16/9;" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>')
            else:
                _page_state['elementos'].append(f'<video controls style="{estilo}"><source src="{_escape_html(url)}"></video>')
            return True

        define('video', video)

        def audio(url):
            _page_state['elementos'].append(f'<audio controls><source src="{_escape_html(url)}"></audio>')
            return True

        define('audio', audio)

        # ══════════════════════════════════════════════════
        # ALERTAS Y MENSAJES
        # ══════════════════════════════════════════════════

        def alerta(mensaje, tipo='info'):
            colores = {
                'info': '#3498db',
                'exito': '#2ecc71', 'success': '#2ecc71',
                'aviso': '#f39c12', 'warning': '#f39c12',
                'error': '#e74c3c', 'danger': '#e74c3c',
            }
            color = colores.get(tipo, '#3498db')
            _page_state['elementos'].append(f'<div class="alert" style="background:{color}20; border-left:4px solid {color}; padding:15px; margin:10px 0;">{_escape_html(mensaje)}</div>')
            return True

        define('alerta', alerta)
        define('alert', alerta)
        define('mensaje', alerta)
        define('message', alerta)

        def codigo(contenido, lenguaje=None):
            _page_state['elementos'].append(f'<pre><code>{_escape_html(contenido)}</code></pre>')
            return True

        define('codigo', codigo)
        define('code', codigo)

        def cita(texto, autor=None):
            html = f'<blockquote><p>{_escape_html(texto)}</p>'
            if autor:
                html += f'<cite>— {_escape_html(autor)}</cite>'
            html += '</blockquote>'
            _page_state['elementos'].append(html)
            return True

        define('cita', cita)
        define('quote', cita)
        define('blockquote', cita)

        # ══════════════════════════════════════════════════
        # HTML DIRECTO (para control total)
        # ══════════════════════════════════════════════════

        def html_directo(contenido):
            _page_state['elementos'].append(str(contenido))
            return True

        define('html_directo', html_directo)
        define('html_raw', html_directo)
        define('raw_html', html_directo)
        define('html', html_directo)

        def estilo_extra(css):
            _page_state['estilos_extra'] += str(css)
            return True

        define('estilo_extra', estilo_extra)
        define('extra_css', estilo_extra)
        define('css', estilo_extra)

        def script_extra(js):
            _page_state['scripts_extra'] += str(js)
            return True

        define('script_extra', script_extra)
        define('extra_js', script_extra)
        define('javascript', script_extra)
        define('js', script_extra)

        # ══════════════════════════════════════════════════
        # GENERAR HTML FINAL
        # ══════════════════════════════════════════════════

        def generar_html():
            tema = _get_tema()
            fuente = _page_state['fuente']

            css = f'''
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: {fuente}, sans-serif;
                background: {tema['fondo']};
                color: {tema['texto']};
                line-height: 1.6;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3, h4, h5, h6 {{ margin: 20px 0 10px 0; color: {tema['texto']}; }}
            p {{ margin: 10px 0; }}
            a {{ color: {tema['primario']}; }}
            img {{ max-width: 100%; height: auto; border-radius: 8px; }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
                transition: opacity 0.3s;
            }}
            .btn:hover {{ opacity: 0.8; }}
            .card {{
                background: {tema['tarjeta']};
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border: 1px solid {tema['borde']};
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .row {{ display: flex; flex-wrap: wrap; margin: -10px; }}
            .col {{ flex: 1; padding: 10px; min-width: 250px; }}
            section {{ margin: 30px 0; }}
            hr {{ border: none; border-top: 1px solid {tema['borde']}; margin: 20px 0; }}
            .form-group {{ margin: 15px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .form-group input, .form-group textarea, .form-group select {{
                width: 100%;
                padding: 12px;
                border: 1px solid {tema['borde']};
                border-radius: 6px;
                font-size: 16px;
                background: {tema['fondo']};
                color: {tema['texto']};
            }}
            .form-group textarea {{ min-height: 100px; resize: vertical; }}
            .table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            .table th, .table td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid {tema['borde']};
            }}
            .table th {{ background: {tema['tarjeta']}; font-weight: bold; }}
            .table tr:hover {{ background: {tema['tarjeta']}; }}
            blockquote {{
                border-left: 4px solid {tema['primario']};
                padding: 15px 20px;
                margin: 15px 0;
                background: {tema['tarjeta']};
                border-radius: 0 8px 8px 0;
            }}
            blockquote cite {{ display: block; margin-top: 10px; color: {tema['primario']}; }}
            pre {{
                background: {tema['tarjeta']};
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                border: 1px solid {tema['borde']};
            }}
            code {{ font-family: monospace; }}
            ul, ol {{ margin: 10px 0; padding-left: 30px; }}
            li {{ margin: 5px 0; }}
            @media (max-width: 768px) {{
                .row {{ flex-direction: column; }}
                .col {{ min-width: 100%; }}
            }}
            {_page_state['estilos_extra']}
            '''

            contenido = '\n'.join(_page_state['elementos'])

            html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_escape_html(_page_state['titulo'])}</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        {contenido}
    </div>
    <script>{_page_state['scripts_extra']}</script>
</body>
</html>'''
            return html

        define('generar_html', generar_html)
        define('generate_html', generar_html)
        define('build_html', generar_html)
        define('construir_html', generar_html)

        def web_guardar(path):
            html = generar_html()
            dir_path = os.path.dirname(str(path))
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(str(path), 'w', encoding='utf-8') as f:
                f.write(html)
            return True

        define('web_guardar', web_guardar)
        define('web_save', web_guardar)
        define('guardar_web', web_guardar)
        define('save_web', web_guardar)

        def web_servir(puerto=8080):
            html = generar_html()

            def handler(req):
                return {'body': html, 'status': 200, 'content_type': 'text/html; charset=utf-8'}

            from http.server import HTTPServer, BaseHTTPRequestHandler

            class SimpleHandler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))

            server = HTTPServer(('0.0.0.0', int(puerto)), SimpleHandler)
            print(f"🌐 Web Mesa en http://localhost:{puerto}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 Servidor detenido")
                server.shutdown()

        define('web_servir', web_servir)
        define('web_serve', web_servir)
        define('servir_web', web_servir)
        define('serve_web', web_servir)

        # ══════════════════════════════════════════════════
        # TEMPLATES PREDEFINIDOS
        # ══════════════════════════════════════════════════

        def web_landing(titulo_principal, subtitulo=None, boton_texto=None, boton_url=None):
            _reset_page()
            _page_state['titulo'] = str(titulo_principal)
            tema = _get_tema()
            html = f'''
            <div style="text-align:center; padding:100px 20px;">
                <h1 style="font-size:3em; margin-bottom:20px;">{_escape_html(titulo_principal)}</h1>
            '''
            if subtitulo:
                html += f'<p style="font-size:1.3em; color:{tema["texto"]}; opacity:0.8; margin-bottom:30px;">{_escape_html(subtitulo)}</p>'
            if boton_texto and boton_url:
                html += f'<a href="{_escape_html(boton_url)}" class="btn" style="background:{tema["primario"]}; font-size:1.2em; padding:15px 40px;">{_escape_html(boton_texto)}</a>'
            html += '</div>'
            _page_state['elementos'].append(html)
            return True

        define('web_landing', web_landing)
        define('landing', web_landing)

        def web_blog(titulo, posts):
            _reset_page()
            _page_state['titulo'] = str(titulo)
            titulo_elem(titulo, 1)
            for post in posts:
                if isinstance(post, dict):
                    t = post.get('titulo', post.get('title', 'Sin título'))
                    c = post.get('contenido', post.get('content', ''))
                    f = post.get('fecha', post.get('date', ''))
                    tarjeta_inicio(t)
                    if f:
                        texto(f, 'italica')
                    texto(c)
                    tarjeta_fin()
            return True

        # Referencia a titulo (ya definido arriba)
        titulo_elem = titulo

        define('web_blog', web_blog)
        define('blog', web_blog)

        def web_portfolio(nombre, descripcion, proyectos):
            _reset_page()
            _page_state['titulo'] = str(nombre)
            tema = _get_tema()

            html = f'''
            <div style="text-align:center; padding:50px 0;">
                <h1>{_escape_html(nombre)}</h1>
                <p style="font-size:1.2em; opacity:0.8;">{_escape_html(descripcion)}</p>
            </div>
            <h2>Proyectos</h2>
            <div class="row">
            '''
            for p in proyectos:
                if isinstance(p, dict):
                    t = p.get('titulo', p.get('title', ''))
                    d = p.get('descripcion', p.get('description', ''))
                    img = p.get('imagen', p.get('image', ''))
                    url = p.get('url', p.get('link', '#'))
                    html += '<div class="col"><div class="card">'
                    if img:
                        html += f'<img src="{_escape_html(img)}" style="width:100%; border-radius:8px; margin-bottom:10px;">'
                    html += f'<h3>{_escape_html(t)}</h3>'
                    html += f'<p>{_escape_html(d)}</p>'
                    html += f'<a href="{_escape_html(url)}" class="btn" style="background:{tema["primario"]};">Ver más</a>'
                    html += '</div></div>'
            html += '</div>'
            _page_state['elementos'].append(html)
            return True

        define('web_portfolio', web_portfolio)
        define('portfolio', web_portfolio)

# ============================================================
# FUNCIONAL
# ============================================================

class MesaFunctional:

    @staticmethod
    def register(env, define, interpreter):

        def _call(func, args):
            if isinstance(func, MesaFunc):
                return interpreter._call_func(func, args)
            elif callable(func):
                return func(*args)
            return None

        def mapear(func, lista):
            return [_call(func, [x]) for x in lista]

        define('mapear', mapear)
        define('map_list', mapear)

        def filtrar(func, lista):
            return [x for x in lista if _call(func, [x])]

        define('filtrar', filtrar)
        define('filter_list', filtrar)

        def reducir(func, lista, inicial=None):
            if inicial is not None:
                acc = inicial
                for item in lista:
                    acc = _call(func, [acc, item])
                return acc
            else:
                if not lista:
                    return None
                acc = lista[0]
                for item in lista[1:]:
                    acc = _call(func, [acc, item])
                return acc

        define('reducir', reducir)
        define('reduce', reducir)

        def cada(func, lista):
            return all(_call(func, [x]) for x in lista)

        define('cada', cada)
        define('every', cada)
        define('todos', cada)

        def alguno(func, lista):
            return any(_call(func, [x]) for x in lista)

        define('alguno', alguno)
        define('some', alguno)
        define('cualquiera', alguno)

        def encontrar(func, lista):
            for x in lista:
                if _call(func, [x]):
                    return x
            return None

        define('encontrar', encontrar)
        define('find', encontrar)

        def encontrar_indice(func, lista):
            for i, x in enumerate(lista):
                if _call(func, [x]):
                    return i
            return -1

        define('encontrar_indice', encontrar_indice)
        define('find_index', encontrar_indice)

        def agrupar(func, lista):
            result = {}
            for x in lista:
                key = str(_call(func, [x]))
                if key not in result:
                    result[key] = []
                result[key].append(x)
            return result

        define('agrupar', agrupar)
        define('group_by', agrupar)

        def zip_listas(*listas):
            return [list(x) for x in zip(*listas)]

        define('zip_listas', zip_listas)
        define('zip', zip_listas)

        def enumerar_lista(lista, inicio=0):
            return [[i, v] for i, v in enumerate(lista, start=int(inicio))]

        define('enumerar', enumerar_lista)
        define('enumerate', enumerar_lista)

        def aplanar(lista):
            result = []
            for item in lista:
                if isinstance(item, list):
                    result.extend(aplanar(item))
                else:
                    result.append(item)
            return result

        define('aplanar_lista', aplanar)
        define('flatten', aplanar)

        def unico(lista):
            seen = []
            result = []
            for item in lista:
                if item not in seen:
                    seen.append(item)
                    result.append(item)
            return result

        define('unico', unico)
        define('unique', unico)

        def partir(lista, tamanio):
            tamanio = int(tamanio)
            return [lista[i:i+tamanio] for i in range(0, len(lista), tamanio)]

        define('partir', partir)
        define('chunk', partir)

        def tomar(lista, n):
            return lista[:int(n)]

        def saltar_n(lista, n):
            return lista[int(n):]

        define('tomar', tomar)
        define('take', tomar)
        define('saltar_n', saltar_n)
        define('drop', saltar_n)


# ============================================================
# REGISTRAR TODO
# ============================================================

def register_stdlib(interpreter):
    env = interpreter.env
    define = env.define

    MesaFilesystem.register(env, define, interpreter)
    MesaHTTP.register(env, define, interpreter)
    MesaHTTPServer.register(env, define, interpreter)
    MesaJSON.register(env, define, interpreter)
    MesaRegex.register(env, define, interpreter)
    MesaCrypto.register(env, define, interpreter)
    MesaDatabase.register(env, define, interpreter)
    MesaConcurrency.register(env, define, interpreter)
    MesaCSV.register(env, define, interpreter)
    MesaCompression.register(env, define, interpreter)
    MesaDateTime.register(env, define, interpreter)
    MesaSystem.register(env, define, interpreter)
    MesaFunctional.register(env, define, interpreter)
    MesaWebBuilder.register(env, define, interpreter)  # <-- AGREGAR ESTA LÍNEA