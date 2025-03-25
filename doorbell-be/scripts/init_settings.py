import json
import asyncio
import os
from datetime import datetime

import asyncpg

from dotenv import load_dotenv

load_dotenv()

async def import_settings():
    with open('../doorbell_controller/settings.json', 'r') as f:
        config = json.load(f)

    button_debounce = config['button']['debounce']
    button_polling_rate = int(config['button']['polling_rate'] * 1000)  # Convert to milliseconds if needed

    motion_sensor_debounce = config['motion_sensor']['debounce']
    motion_sensor_polling_rate = int(
        config['motion_sensor']['polling_rate'] * 1000)  # Convert to milliseconds if needed

    camera_bitrate = config['camera']['streaming']['bitrate']
    camera_stop_motion_interval = int(config['camera']['stop_motion']['interval'] * 1000)  # Convert to milliseconds
    camera_stop_motion_duration = config['camera']['stop_motion']['duration']

    color_r = config['rgb']['color']['R']
    color_g = config['rgb']['color']['G']
    color_b = config['rgb']['color']['B']

    env = os.environ.get('ENV', 'LOCAL').upper()
    connection_string = os.environ[f'DB_CONNECTION_STRING_{env}']

    conn = await asyncpg.connect(connection_string)

    await conn.execute('DELETE FROM settings')

    current_time = datetime.now()
    await conn.execute('''
            INSERT INTO settings(
                id,
                button_debounce, 
                button_polling_rate, 
                motion_sensor_debounce, 
                motion_sensor_polling_rate,
                camera_bitrate,
                camera_stop_motion_interval,
                camera_stop_motion_duration,
                color_r,
                color_g,
                color_b,
                created_at,
                modified_at
            ) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ''',
        1,
        button_debounce,
        button_polling_rate,
        motion_sensor_debounce,
        motion_sensor_polling_rate,
        camera_bitrate,
        camera_stop_motion_interval,
        camera_stop_motion_duration,
        color_r,
        color_g,
        color_b,
        current_time,
        current_time
    )

    print("Settings imported successfully")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(import_settings())