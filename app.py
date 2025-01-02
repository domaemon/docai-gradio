import gradio as gr
from appsutil import process_document

demo = gr.Interface(
    fn=process_document,
    inputs=gr.Image(type='filepath'),
    outputs=[
        gr.Image(label="docai-image"),
        gr.Textbox(label="docai-summary"),
        gr.Textbox(label="vertex-summary"),
    ],
    examples=[
        ["/app/cloud-storage/image1.jpg"],
        ["/app/cloud-storage/image2.jpg"]
    ]
    #allow_flagging="never" 
)

demo.launch(share=True, allowed_paths=["/app/cloud-storage"])

