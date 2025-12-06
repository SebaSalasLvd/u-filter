import os
import glob
import psycopg2
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_db_conn_params():
    user = os.getenv('DB_USER')
    name = os.getenv('DB_NAME')
    password = os.getenv('DB_PASSWORD', '')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    if not user or not name:
        raise RuntimeError('Faltan variables de entorno DB_USER o DB_NAME')
    return dict(user=user, password=password, host=host, port=port, dbname=name)


def apply_sql_file(cur, path):
    logging.info('Aplicando: %s', path)
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        cur.execute(sql)
    except Exception as e:
        logging.error('Error ejecutando %s: %s', path, e)
        raise


def main():
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    mode = 'up'
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        mode = 'reset'
        logging.info("Modo RESET activado: Se eliminarán las tablas antes de crearlas.")

    params = get_db_conn_params()
    conn = None
    try:
        conn = psycopg2.connect(**params)
        conn.autocommit = False
        cur = conn.cursor()

        if mode == 'reset':
            pattern_down = os.path.join(migrations_dir, '*_down.sql')
            files_down = sorted(glob.glob(pattern_down), reverse=True)
            
            if not files_down:
                logging.warning("No se encontraron archivos *_down.sql para resetear.")
            
            for fpath in files_down:
                apply_sql_file(cur, fpath)

        pattern_up = os.path.join(migrations_dir, '*_up.sql')
        files_up = sorted(glob.glob(pattern_up))
        
        if not files_up:
            logging.info('No se encontraron archivos de migración UP en %s', migrations_dir)
            return

        for fpath in files_up:
            apply_sql_file(cur, fpath)

        conn.commit()
        logging.info('Migraciones aplicadas correctamente.')

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error('Fallo al aplicar migraciones: %s', e)
        raise
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error('Proceso terminado con error: %s', e)
        raise
