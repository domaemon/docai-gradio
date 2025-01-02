import os
import logging
import shutil
from google.cloud import documentai_v1 as documentai
from PIL import Image, ImageDraw
from google import genai
from google.genai import types

def process_document(image_path):
    outputs = [None, None, None]
    
    docai_entities = {}

    if check_cloud_run():
        image_name = os.path.basename(image_path)
        new_image_path = '/app/cloud-storage/' + image_name
        #copy to the cloud storage
        shutil.copy2(image_path, new_image_path)
        image_path = new_image_path
    else:
        print("Running locally")

    docai_image, docai_summary, docai_entities = process_docai(image_path)
    yield[docai_image, docai_summary, None]

    vertex_summary = process_vertex(image_path, docai_summary)

    yield[docai_image, docai_summary, vertex_summary]
    #return docai_image, docai_summary, vertex_summary

def process_docai(image_path):
    docai_entities = {}

    # Read the file into memory
    with open(image_path, "rb") as image:
        image_content = image.read()

    # Load Binary Data into Document AI RawDocument Object
    raw_document = documentai.RawDocument(
        content=image_content, mime_type="image/jpeg"  # Or the appropriate MIME type
    )

    # The full resource name of the processor, e.g.:
    project = os.environ.get('PROJECT')
    location = os.environ.get('DOCAI_REGION')
    processor_id = os.environ.get('DOCAI_PROCESSOR_ID')

    name = f"projects/{project}/locations/{location}/processors/{processor_id}"

    # Configure the process request
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)

    client = documentai.DocumentProcessorServiceClient()

    result = client.process_document(request=request)
    document = result.document

    # Extract and print the desired information from the 'document' object
    # This will depend on the type of document and processor you are using
    # For example, to extract text:
    #print(f"Text: {document.text}")
    
    # Load the image using Pillow
    docai_image = Image.open(image_path) 
    draw = ImageDraw.Draw(docai_image)

    # Example: Access entities (key-value pairs)
    for entity in document.entities:
        value = entity.mention_text
        if entity.normalized_value:
            value = entity.normalized_value.text

        docai_entities[entity.type_] = value

        # Iterate through the extracted entities and draw bounding boxes
        # Get bounding box coordinates
        vertices = entity.page_anchor.page_refs[0].bounding_poly.normalized_vertices
        x1 = int(vertices[0].x * docai_image.width)
        y1 = int(vertices[0].y * docai_image.height)
        x2 = int(vertices[2].x * docai_image.width)
        y2 = int(vertices[2].y * docai_image.height)

        # Draw the bounding box using Pillow
        draw.rectangle([x1, y1, x2, y2], outline="green", width=8)

    docai_summary = f"This is a notice for your National Pension contribution from {docai_entities['payment-period-start']} to {docai_entities['payment-period-end']}. The amount due is {docai_entities['payment-amount']}, and you have until {docai_entities['payment-deadline']} to pay it."
    
    return docai_image, docai_summary, docai_entities

def process_vertex(image_path, docai_summary):
    client = genai.Client(
        vertexai=True,
        project=os.environ.get('PROJECT'),
        location='us-central1'
    )

    with open(image_path, 'rb') as image_file:
        # Read the image content
        image_content = image_file.read()

        # Create the request payload
        image1 = types.Part.from_bytes(
            data=image_content,  # Use the image content directly
            mime_type="image/jpeg",
        )

        model = "gemini-2.0-flash-exp"
        contents = [
            types.Content(
                role="user",
                parts=[
                    image1,
                    types.Part.from_text(f"Give me the summary of this image. Use this information to set context.\n {docai_summary}")
                ]
            )
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature = 1,
            top_p = 0.95,
            max_output_tokens = 8192,
            response_modalities = ["TEXT"],
            safety_settings = [types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="OFF"
            ),types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="OFF"
            ),types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="OFF"
            ),types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="OFF"
            )],
        )

        # Use generate_content instead of generate_content_stream
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        # Print the entire response text
        return response.text

def check_cloud_run():
    """Checks if the code is running on Cloud Run.

    Returns:
        True if running on Cloud Run, False otherwise.
    """
    return os.environ.get('K_SERVICE') is not None

def check_dir_exists(dir_path):
    """Checks if a directory exists.
    
    Args:
     dir_path: The path to the directory.

    Returns:
     True if the directory exists, False otherwise.
    """
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        if os.access(dir_path, os.W_OK):
            result = "EXISTS WRITABLE"
        else:
            result = "EXISTS NOT WRITABLE"
    else:
        result = "DOES NOT EXIST"
     
    return result

#######
# docai_entities['invoice-date'],
# docai_entities['payment-deadline'],
# docai_entities['payment-amount'],
# docai_entities['payment-period-start'],
# docai_entities['payment-period-end'],
# docai_entities['pensioner-address-zip'],
# docai_entities['pensioner-address-1'],
# docai_entities['pensioner-address-2'],
# docai_entities['pensioner-name']

