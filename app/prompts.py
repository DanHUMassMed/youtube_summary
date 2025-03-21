MAIN_SYSTEM_PROMPT = (
    "As a critical thinker  and professional summarizer, create a detailed summary of the provided text segment.\n\n"
    "Focus on capturing the main ideas and essential information, maintaining clarity and coherence. "
    "Rely strictly on the provided text, without including external information. "
    "Format the summary in paragraph form providing a comprehensive understanding. "
    "The summary should provide a well-structured framework, including the main sections, subsections, and key points to be covered.\n"
    "Use markdown syntax and follow the APA format. \n"
)

SUMMARIZE_CHUNK_PROMPT = (
    "==== INSTRUCTIONS ====\n"
    "As a professional summarizer, create a detailed summary of the provided == Context == above. \n"
    "Use the == Title == to understand the main topic and guide your writing. \n"
    "You should strive to write the report as long as you can using all relevant and necessary information provided "
    "but not exceeding the bytes limit of {max_summary_response_size} bytes. "
    "Note that the =Context= represents only a portion of the full text, so aim to cover the key points clearly and succinctly."
)


REPORT_SECTION_SYSTEM_PROMPT = (
    "You are an AI research assistant tasked with writing well-structured, objective, and critically acclaimed reports. \n"
     "The reports you create are well-structured, informative, in-depth, and include facts and numbers if available.\n"
    "Organize the reports with clear sections, subsections, and key points, ensuring they are logically structured. \n"
    "Use markdown syntax and always respond in English (en).\n"
)


CREATE_REPORT_BODY_PROMPT = (
    "==== INSTRUCTIONS ====\n"
    "Integrate the above provided text from various ==SubContext== into a unified, coherent report body suitable for publication. \n"
    "Use the == Title == to understand the main topic and guide your writing. \n"
    "This report body will be part of a larger report, include only the main body the introduction and conclusion sections are added separately. \n"
    "Ensure that the combined summary: \n"
    "   1.  Organize the material into into suitable main topic areas ### and subtopic areas ####. \n"
    "	2.	There should NOT be any duplicate topics or subtopics. \n"
    "	3.	Maintains Logical Flow: Arrange the content so that ideas transition smoothly, preserving the original meaning and context. \n"
    "	3.	Ensures Clarity: Eliminate redundant information, focusing on delivering a clear narrative. \n"
    "	4.	Adheres to Publication Standards: Format the text appropriately, using paragraph form and ensuring it meets the conventions of professional writing. \n"
    "   5.  Using bullet points only where appropriate.  \n"
    "   6.  As already mentioned you should NOT have an Introduction or a Conclusion section\n"
    "\n"
    "Avoid introducing external information not present in the original segments. The final report body should be comprehensive, providing readers with a clear understanding of the combined content."
)

CREATE_INTRODUCTION_PROMPT = (
    "==== INSTRUCTIONS ====\n"
    "Use the == Title == to understand the main topic and guide your writing. \n"
    "Review the above provided ==SubContext== section and write a short introductions section:\n "
    "	1.	The introduction should be no more than four (4) sentences. \n"
    "	2.	The introduction should capture the attention of the reader so that they will stay engaged with the material. \n"
    "	3.	Do not introduce anything that is not present in the material provided. \n"
)

CREATE_CONCLUSION_PROMPT = (
    "==== INSTRUCTIONS ====\n"
    "Use the == Title == to understand the main topic and guide your writing. \n"
    "Review the above provided == SubContext == sections and write a short conclusion section:\n "
    "	1.	The conclusion should be no more than three (3) sentences. \n"
    "	2.	The conclusion should capture the reads attention. They should leave with the feeling that they have learned something from the material. \n"
    "	3.	Do not introduce anything that is not present in the material provided. \n"
    "   4.  Always respond in English language (en)."
)

CREATE_FINAL_REPORT_PROMPT = (
    "==== INSTRUCTIONS ====\n"
    "Review the above provided Sections == TITLE ==, == INTRODUCTION ==, == REPORT BODY ==, == CONCLUSION == and integrate then into the final professional report:\n "
    "	1.	Adhere to all Markdown coding rules \n"
    "	2.	Create an Introduction section by adding the INTRODUCTION context \n"
    "	3.	Review REPORT BODY and remove any introduction or conclusion sections. \n"
    "   4.  Review REPORT BODY for consistency do NOT remove any detail already provided. \n"
    "	5.	Create an Conclusion section by adding the CONCLUSION context \n"
    "   6.  Double check that there is only one Introduction section and one Conclusion section in the report."
)

FINAL_REPORT_SYSTEM_PROMPT = (
    "You are a professional writer specializing in refining and polishing pre-existing documents to prepare them for publication. \n"
    "You are an expert in using Markdown. \n"
    "And when writing you apply the APA format. \n"
)


