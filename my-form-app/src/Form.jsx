import React from 'react';
import { useForm } from 'react-hook-form';

export default function Form() {
  const { register, handleSubmit } = useForm();

  const onSubmit = async (data) => {
    try {
      const response = await fetch('http://localhost:8080', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
  
      const result = await response.json();
      console.log('✅ Cloud function response:', result);
    } catch (error) {
      console.error('❌ Error:', error);
    }
  };
  
  

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>WPForms</h1>
      <form onSubmit={handleSubmit(onSubmit)} style={styles.form}>
        <label>Subject</label>
        <input {...register("subjectline")} placeholder="Subject" />

        <label>Question</label>
        <textarea {...register("question")} placeholder="Question" />

        <label>Model</label>
        <input {...register("model_name")} defaultValue="gpt-4o" />

        <label>Temperature</label>
        <input type="number" step="0.01" {...register("temperature")} defaultValue={0} />

        <label>Retries</label>
        <input type="number" {...register("max_retries")} defaultValue={0} />

        <label>OpenAI API Key</label>
        <input {...register("openai_api_key")} placeholder="OpenAI API Key" />

        <label>Pinecone API Key</label>
        <input {...register("pinecone_api_key")} placeholder="Pinecone API Key" />

        <label>Vector Store Index Name</label>
        <input {...register("vectorstore")} placeholder="Vector Store Index Name" />

        <label>Saved Reply Vector Store Index Name</label>
        <input {...register("sr_vectorstore")} placeholder="Saved Reply Vector Store Index Name" />

        <button type="submit" style={styles.button}>Submit</button>
      </form>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '500px',
    margin: '50px auto',
    padding: '20px',
    borderRadius: '8px',
    backgroundColor: '#f9f9f9',
    boxShadow: '0 0 10px rgba(0,0,0,0.1)',
  },
  heading: {
    textAlign: 'center',
    marginBottom: '20px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  button: {
    padding: '10px',
    backgroundColor: '#4f46e5',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
  },
};
