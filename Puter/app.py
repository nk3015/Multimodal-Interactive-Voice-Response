from flask import Flask, render_template_string, send_from_directory, abort
import os

app = Flask(__name__)

@app.route('/')
def list_files():
    directory = os.path.dirname(os.path.abspath(__file__))

    # Function to create a tree structure
    def create_tree(path, base_path):
        tree = {'name': os.path.basename(path), 'children': [], 'path': os.path.relpath(path, base_path).replace(os.path.sep, '/')}
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    tree['children'].append(create_tree(item_path, base_path))
                else:
                    if item != os.path.basename(__file__):
                        tree['children'].append({'name': item, 'path': os.path.relpath(item_path, base_path).replace(os.path.sep, '/')})
        except PermissionError as e:
            print(f"PermissionError accessing {path}: {e}")
        return tree

    tree = create_tree(directory, directory)

    # Template for displaying the tree structure with clickable links
    template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Directory Tree</title>
        <style>
            ul, #tree { list-style-type: none; }
            li { margin-left: 20px; }
            .dir { font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Directory Tree</h1>
        <div id="tree"></div>
        <script>
            const treeData = {{ tree|tojson }};
            function renderTree(node) {
                const ul = document.createElement('ul');
                if (node.children) {
                    const li = document.createElement('li');
                    li.classList.add('dir');
                    li.textContent = node.name;
                    ul.appendChild(li);
                    node.children.forEach(child => {
                        ul.appendChild(renderTree(child));
                    });
                } else {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = `/${encodeURIComponent(node.path)}`;
                    a.textContent = node.name;
                    li.appendChild(a);
                    ul.appendChild(li);
                }
                return ul;
            }
            document.getElementById('tree').appendChild(renderTree(treeData));
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(template, tree=tree)

@app.route('/<path:filename>')
def serve_file(filename):
    # Directory is the same as where this Flask script is located
    directory = os.path.dirname(os.path.abspath(__file__))
    try:
        # Ensure the file path is safe to avoid directory traversal attacks
        file_path = os.path.join(directory, filename)
        if os.path.commonprefix([os.path.realpath(file_path), directory]) == directory:
            if os.path.isfile(file_path):
                return send_from_directory(directory, filename)
            else:
                abort(404)  # Return 404 if the file is not found
        else:
            abort(403)  # Return 403 for attempted directory traversal
    except Exception as e:
        print(f"Exception serving file {file_path}: {e}")
        abort(500)  # Return 500 for any other exceptions

if __name__ == '__main__':
    app.run(debug=True)
