import os
import base64
import requests

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

def process_pdf(file_path):
    print(f"[+] Procesando: {file_path}")
    base64_pdf = encode_file_to_base64(file_path)
    document_url = f"data:application/pdf;base64,{base64_pdf}"
    
    headers = {
        "Authorization": "Bearer kSovQ99nQJ2ZKdMMKHPU5KdH5MpkVH6H",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": document_url
        },
        "include_image_base64": True
    }
    
    response = requests.post("https://api.mistral.ai/v1/ocr", headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        markdown_content = []
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        dir_name = os.path.dirname(file_path)
        images_dir_name = f"{base_name}_images"
        images_dir_path = os.path.join(dir_name, images_dir_name)
        
        os.makedirs(images_dir_path, exist_ok=True)
        
        for page in data.get("pages", []):
            page_md = page.get("markdown", "")
            
            for img in page.get("images", []):
                img_id = img.get("id")
                img_b64 = img.get("image_base64")
                
                if img_id and img_b64:
                    img_path = os.path.join(images_dir_path, img_id)
                    clean_b64 = img_b64.split(",")[-1]
                    with open(img_path, "wb") as img_file:
                        img_file.write(base64.b64decode(clean_b64))
                        
                    page_md = page_md.replace(img_id, f"{images_dir_name}/{img_id}")
            
            markdown_content.append(page_md)
        
        output_path = os.path.join(dir_name, f"{base_name}.md")
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write("\n".join(markdown_content))
        print(f"[+] Guardado MD: {output_path}")
        print(f"[+] Imagenes guardadas en: {images_dir_path}")
    else:
        print(f"[-] Error {response.status_code} en {file_path}: {response.text}")

def main():
    base_dir = r"D:\Users\Lithium\Desktop\Work\UAH - FIIA 2026\CESFAM\Model\Consume"
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                process_pdf(full_path)

if __name__ == "__main__":
    main()