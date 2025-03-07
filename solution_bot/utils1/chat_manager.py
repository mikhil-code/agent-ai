from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

class ChatManager:
    def __init__(self, vector_store):
        self.llm = ChatOpenAI(temperature=0)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True
        )
        self.qa_template = """
        You are a precise and accurate assistant that only answers based on the given context. 
        
        Context: {context}
        
        Question: {question}
        
        Instructions:
        1. Answer ONLY based on the information provided in the context
        2. If the answer cannot be fully derived from the context, say "I cannot provide a complete answer based on the available information"
        3. Do not make assumptions or add information not present in the context
        4. If you're unsure about any part of the answer, acknowledge the uncertainty
        5. Include specific references or quotes from the document where relevant
        
        Answer:"""
        
        self.follow_up_template = """
        Based on the previous answer from the document context, suggest 3 relevant follow-up questions.
        Previous question: {question}
        Previous answer: {answer}
        
        Generate only questions that can be answered using the document content.
        Each question should explore a different aspect mentioned in the previous answer.
        Make questions specific and directly related to the context.
        
        Return exactly 3 questions, one per line.
        """
        
        self.chain = self._create_chain(vector_store)
    
    def _create_chain(self, vector_store):
        if (vector_store.vector_store is None):
            return None
            
        qa_prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["context", "question"]
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vector_store.vector_store.as_retriever(search_kwargs={"k": 4}),
            memory=self.memory,
            return_source_documents=True,
            chain_type="stuff",
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            get_chat_history=lambda h: h,
            output_key="answer"  # Explicitly set the output key
        )
    
    def generate_follow_up_questions(self, question, answer):
        if self.llm is None:
            return []
        
        try:
            prompt = PromptTemplate(
                template=self.follow_up_template,
                input_variables=["question", "answer"]
            )
            
            response = self.llm.predict(prompt.format(
                question=question,
                answer=answer
            ))
            
            # Split response into individual questions
            questions = [q.strip() for q in response.split('\n') if q.strip()]
            return questions[:3]  # Ensure we return max 3 questions
            
        except Exception as e:
            return []

    def get_response(self, query):
        if self.chain is None:
            return "Please upload a document first.", []
            
        try:
            response = self.chain({"question": query})
            answer = response['answer']
            
            # Generate follow-up questions only if we have a valid answer
            follow_up_questions = []
            if not ("I cannot provide" in answer or "not enough information" in answer):
                follow_up_questions = self.generate_follow_up_questions(query, answer)
            
            return answer, follow_up_questions
                
        except Exception as e:
            return f"Error: {str(e)}", []
