
from .perf_build_docker import build_and_measure

def run(original_code, optimized_code, build_context):

    print('Docker dynamic build analysis...\n\n')
    print('stiamo per fare build di original')
    original = build_and_measure(original_code, build_context, tag="original_img")
    print('stiamo pòer fare build di optimized')
    optimized = build_and_measure(optimized_code, build_context, tag="optimized_img")

    result = {
        'original':original,
        'optimized':optimized
    }

    if original['success'] and optimized['success']:

        result['improvements'] = {
            'build_time_save': round(original['build_time']-optimized['build_time'], 2),
            'sice_saved_mb': round(original['image_size_mb']-optimized['image_size_mb'], 2),
            'layer_saved': original['layers']-optimized['layers']
        }
    else:
        result['improvements'] = None

        result['comparison_status'] = (
            "Quantitative comparison not available because "
            "at least one Docker image could not be built."
        )

    print('\n---- Dynamic Build Analysis ----')
    print(result)

    return result

    def diff(a, b):

        return {
            'original': a,
            'optimized': b,
            'improvements': {
                    "build_time_saved": round(a["build_time"] - b["build_time"], 2),
                    "size_saved_mb": round(a["image_size_mb"] - b["image_size_mb"], 2),
                    "layer_saved": a["layers"] - b["layers"]
                    }
                }
    result = diff(original, optimized)

    print('---- Dynamic Build Analysis ---\n')
    print(result)
    return result
