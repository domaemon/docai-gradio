import gradio as gr
from appsutil import process_document

demo = gr.Interface(
    fn=process_document,
    inputs=gr.Image(type='filepath'),
    outputs=[
             gr.Image(label="docai-image"),
             gr.Text(label="docai-summary"),
             gr.Markdown(label="vertex-summary"),
             ],
    #allow_flagging="never" 
)

demo.launch(share=True)

