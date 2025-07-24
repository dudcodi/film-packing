from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rectpack import newPacker, MaxRectsBssf, MaxRectsBaf, SkylineMwfl, SkylineBl, GuillotineBssfSas

app = Flask(__name__)
CORS(app)

# 비교할 알고리즘 목록 (원하면 추가/삭제 가능)
ALGO_LIST = [
    ("MaxRectsBssf", MaxRectsBssf),
    ("MaxRectsBaf", MaxRectsBaf),
    ("SkylineMwfl", SkylineMwfl),
    ("SkylineBl", SkylineBl),
    ("GuillotineBssfSas", GuillotineBssfSas),
]

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.get_json()
        rects = data['rects']
        canvas_width = data.get('canvas_width', 150)
        allow_rotate = data.get('allow_rotate', True)
        canvas_maxlen = data.get('canvas_maxlen', 3000)

        # (큰 것부터 내림차순 정렬하면 효과 ↑)
        sorted_rects = sorted(
            [(int(r['width']), int(r['height']), idx) for idx, r in enumerate(rects)],
            key=lambda x: max(x[0], x[1]), reverse=True
        )
        rect_map = {i: r for i, r in enumerate(rects)}

        results = {}
        for algo_name, algo_class in ALGO_LIST:
            packer = newPacker(rotation=allow_rotate, pack_algo=algo_class)
            for w, h, rid in sorted_rects:
                packer.add_rect(w, h, rid)
            packer.add_bin(int(canvas_width), int(canvas_maxlen))
            packer.pack()

            packed = []
            used_length = 0
            for abin in packer:
                for rect in abin:
                    x, y = rect.x, rect.y
                    w, h = rect.width, rect.height
                    rid = rect.rid
                    orig = rect_map[rid]
                    rotated = not (orig['width'] == w and orig['height'] == h)
                    packed.append({
                        "id": rid + 1,
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "rotated": rotated
                    })
                    used_length = max(used_length, y + h)
            results[algo_name] = {
                "packed": packed,
                "used_length": used_length
            }

        # "최단길이 알고리즘" 추천도 같이 포함
        min_algo = min(results.items(), key=lambda kv: kv[1]["used_length"])
        results["_best_algo"] = min_algo[0]
        results["_best_length"] = min_algo[1]["used_length"]

        return jsonify(results)
    except Exception as e:
        print('Error in /optimize:', e)
        return jsonify({"error": str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)