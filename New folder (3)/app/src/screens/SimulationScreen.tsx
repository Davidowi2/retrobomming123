import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import type { User } from '../App';

interface SimulationScreenProps {
  user: User;
  onComplete: () => void;
}

interface Question {
  question_id: string;
  order_index: number;
  question_text: string;
  answer_options: Record<string, string>;
}

interface SimulationState {
  session_id: string;
  job_type_name: string;
  level: string;
  total_questions: number;
  current_question: Question | null;
  progress: {
    answered: number;
    total: number;
  };
  section: 'knowledge' | 'mini_task';
  mini_task?: {
    description: string;
    submission_type: string;
    time_limit_minutes: number;
  };
}

export function SimulationScreen({ onComplete }: SimulationScreenProps) {
  const [simulation, setSimulation] = useState<SimulationState | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [sessionExpired, setSessionExpired] = useState(false);

  // For mini-task
  const [miniTaskContent, setMiniTaskContent] = useState('');
  const [miniTaskFile, setMiniTaskFile] = useState<File | null>(null);

  // Start simulation on mount
  useEffect(() => {
    startSimulation();
  }, []);

  // Heartbeat to keep session alive
  useEffect(() => {
    if (!simulation?.session_id) return;

    const heartbeat = setInterval(async () => {
      try {
        const status = await api.sessionHeartbeat(simulation.session_id);
        if (!status.session_active) {
          setSessionExpired(true);
          clearInterval(heartbeat);
        }
      } catch (error) {
        console.error('Heartbeat failed:', error);
      }
    }, 60000); // Every minute

    return () => clearInterval(heartbeat);
  }, [simulation?.session_id]);

  const startSimulation = async () => {
    setIsLoading(true);
    setError('');

    try {
      // For demo, start Data Cleaning beginner simulation
      // In real app, this would come from user selection
      const response = await api.startSimulation(
        '00000000-0000-0000-0000-000000000001', // Demo job type ID
        'beginner'
      );

      setSimulation({
        session_id: response.session_id,
        job_type_name: response.job_type_name,
        level: response.level,
        total_questions: response.total_questions,
        current_question: response.first_question,
        progress: { answered: 0, total: response.total_questions },
        section: 'knowledge',
      });
      setStartTime(Date.now());
    } catch (err: any) {
      setError(err.message || 'Failed to start simulation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!simulation?.current_question || !selectedAnswer) return;

    setIsSubmitting(true);
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    try {
      const response = await api.submitAnswer(
        simulation.session_id,
        simulation.current_question.question_id,
        selectedAnswer,
        timeSpent
      );

      if (response.section_complete) {
        // Transition to mini-task
        setSimulation(prev => ({
          ...prev!,
          section: 'mini_task',
          mini_task: response.mini_task,
          progress: { answered: response.progress.answered, total: response.progress.total },
        }));
      } else if (response.next_question) {
        // Show next question
        setSimulation(prev => ({
          ...prev!,
          current_question: response.next_question,
          progress: { answered: response.progress.answered, total: response.progress.total },
        }));
        setSelectedAnswer(null);
        setStartTime(Date.now());
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit answer');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitMiniTask = async () => {
    if (!simulation) return;

    setIsSubmitting(true);

    try {
      await api.submitMiniTask(
        simulation.session_id,
        miniTaskContent,
        miniTaskFile || undefined
      );

      onComplete();
    } catch (err: any) {
      setError(err.message || 'Failed to submit mini-task');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="screen-container flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-3 border-[#FF6B2B] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-[#A0A2A8]">Preparing your simulation...</p>
        </div>
      </div>
    );
  }

  if (sessionExpired) {
    return (
      <div className="screen-container flex items-center justify-center">
        <div className="card max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-500/10 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Session Expired</h2>
          <p className="text-[#A0A2A8] mb-6">
            Your session expired due to inactivity. Your progress has been saved.
          </p>
          <button onClick={startSimulation} className="btn btn-primary">
            Restart Simulation
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="screen-container flex items-center justify-center">
        <div className="card max-w-md text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button onClick={startSimulation} className="btn btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!simulation) return null;

  // Mini-task section
  if (simulation.section === 'mini_task' && simulation.mini_task) {
    return (
      <div className="screen-container">
        <div className="max-w-2xl mx-auto w-full">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <span className="text-sm text-[#FF6B2B]">Mini Task</span>
              <h2 className="text-xl font-bold text-white">{simulation.job_type_name}</h2>
            </div>
            <div className="text-right">
              <span className="text-sm text-[#6B6D75]">Time Limit</span>
              <p className="text-white font-mono">{simulation.mini_task.time_limit_minutes}:00</p>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-[#A0A2A8]">Overall Progress</span>
              <span className="text-white">Knowledge Complete ✓</span>
            </div>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: '68%' }} />
            </div>
          </div>

          {/* Task Description */}
          <div className="card mb-6">
            <h3 className="font-semibold text-white mb-3">Task Description</h3>
            <p className="text-[#A0A2A8] whitespace-pre-line">{simulation.mini_task.description}</p>
          </div>

          {/* Submission Area */}
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Your Submission</h3>
            
            {simulation.mini_task.submission_type === 'text_editor' && (
              <textarea
                value={miniTaskContent}
                onChange={(e) => setMiniTaskContent(e.target.value)}
                placeholder="Enter your response here..."
                className="input min-h-[200px] resize-y"
              />
            )}
            
            {simulation.mini_task.submission_type === 'file_upload' && (
              <div className="border-2 border-dashed border-[#1E1F24] rounded-lg p-8 text-center">
                <input
                  type="file"
                  onChange={(e) => setMiniTaskFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="w-12 h-12 mx-auto mb-4 bg-[#1E1F24] rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-[#A0A2A8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-white mb-1">
                    {miniTaskFile ? miniTaskFile.name : 'Click to upload file'}
                  </p>
                  <p className="text-sm text-[#6B6D75]">
                    CSV, XLSX, or PDF files accepted
                  </p>
                </label>
              </div>
            )}
            
            {simulation.mini_task.submission_type === 'interactive_form' && (
              <div className="space-y-4">
                <p className="text-[#A0A2A8]">Complete the form below:</p>
                <input
                  type="text"
                  placeholder="Answer 1"
                  className="input"
                />
                <input
                  type="text"
                  placeholder="Answer 2"
                  className="input"
                />
              </div>
            )}

            <button
              onClick={handleSubmitMiniTask}
              disabled={isSubmitting || (!miniTaskContent && !miniTaskFile)}
              className="btn btn-primary w-full mt-6"
            >
              {isSubmitting ? (
                <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              ) : (
                'Submit Task'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Knowledge questions section
  if (!simulation.current_question) {
    return (
      <div className="screen-container flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-[#FF6B2B] border-t-transparent rounded-full" />
      </div>
    );
  }

  const question = simulation.current_question;
  const progressPercent = (simulation.progress.answered / simulation.progress.total) * 100;

  return (
    <div className="screen-container">
      <div className="max-w-2xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <span className="text-sm text-[#FF6B2B]">{simulation.job_type_name}</span>
            <h2 className="text-xl font-bold text-white capitalize">{simulation.level} Level</h2>
          </div>
          <div className="text-right">
            <span className="text-sm text-[#6B6D75]">Question</span>
            <p className="text-white font-mono">{question.order_index}/{simulation.total_questions}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="progress-bar">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${progressPercent}%` }} 
            />
          </div>
        </div>

        {/* Question */}
        <div className="card mb-6">
          <h3 className="text-lg text-white mb-6 leading-relaxed">
            {question.question_text}
          </h3>

          <div className="space-y-3">
            {Object.entries(question.answer_options).map(([key, value]) => (
              <div
                key={key}
                onClick={() => setSelectedAnswer(key)}
                className={`option-card ${selectedAnswer === key ? 'selected' : ''}`}
              >
                <span className="option-letter">{key}</span>
                <span className="text-white">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmitAnswer}
          disabled={!selectedAnswer || isSubmitting}
          className="btn btn-primary w-full"
        >
          {isSubmitting ? (
            <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
          ) : simulation.progress.answered === simulation.progress.total - 1 ? (
            'Complete Section'
          ) : (
            'Next Question'
          )}
        </button>

        {/* Info */}
        <p className="text-center text-sm text-[#6B6D75] mt-4">
          Knowledge Section (68% of total score)
        </p>
      </div>
    </div>
  );
}
