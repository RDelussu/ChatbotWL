import time
import docker
import tempfile
import os
import shutil

client = docker.from_env()

def build_and_measure(dockerfile_content, build_context, tag):

    tmp_dir = tempfile.mkdtemp()

    shutil.copytree(
        build_context,
        tmp_dir,
        dirs_exist_ok=True
    )

    dockerfile_path = os.path.join(tmp_dir, 'Dockerfile')

    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)

    print('DOCKERFILE CONTENT -- CAPIAMO COSA ABBIAMO LI DENTRO\n')
    print(dockerfile_content)
    print('====================================================\n')
    start = time.time()
    try:
        image, logs = client.images.build(path=tmp_dir, tag=tag, rm=True)
    
        end = time.time()
    
        build_time = end - start
        
        size_mb = image.attrs['Size'] / 1024 / 1024
        layers = len(image.attrs['RootFS']['Layers'])
    
        # cleanup (remove docker container)
        try: 
            client.images.remove(image.id, force=True)
        except Exception:
            pass

        return {
            'success': True, 
            'build_time': round(build_time, 2),
            'image_size_mb': round(size_mb, 2),
            'layers': layers,
            'error': None
        }
    except docker.errors.BuildError as e:
        end = time.time()

        error_message = str(e)

        try:
            if e.build_log:
                for log in e.build_log:
                    if 'stream' in log:
                        error_message += '\n' + log['stream'].strip()
                    elif 'error' in log:
                        error_message += '\n' + log['error'].strip()
        except Exception:
            pass
        return {
            'success': False, 
            'build_time': round(end-start, 2),
            'image_size_mb':None, 
            'layers':None,
            'error':error_message
        }
    finally:
        try:
            os.remove(dockerfile_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass


