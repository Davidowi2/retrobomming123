import { useState, useEffect } from 'react';
import type { User } from '../App';

interface ResultsScreenProps {
  user: User;
  onBackToSkills: () => void;
}

interface SimulationResult {
  session_id: string;
  status: string;
  overall_passed: boolean;
  scores: {
    knowledge: {
      score: number;
      passed: boolean;
    };
    mini_task: {
      score: number;
      passed: boolean;
    };
    overall: number;
  };
  rank: {
    previous: string;
    new: string;
    promoted: boolean;
  };
  skill_dna: {
    is_first_time: boolean;
    strengths: string[];
    weaknesses: string[];
    chart_data: Array<{
      concept: string;
      strength: number;
    }>;
  };
  next_steps: {
    can_retake: boolean;
    next_retake_available_at: string | null;
    can_level_up: boolean;
  };
}

export function ResultsScreen({ onBackToSkills }: ResultsScreenProps) {
  const [results, setResults] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // For demo, we'll show mock results
    // In real app, fetch from API using session ID
    const mockResults: SimulationResult = {
      session_id: 'demo-session',
      status: 'completed',
      overall_passed: true,
      scores: {
        knowledge: {
          score: 85,
          passed: true,
        },
        mini_task: {
          score: 78,
          passed: true,
        },
        overall: 82.76,
      },
      rank: {
        previous: 'beginner',
        new: 'intermediate',
        promoted: true,
      },
      skill_dna: {
        is_first_time: true,
        strengths: ['Missing Values', 'Duplicate Records'],
        weaknesses: ['Mixed Date Formats'],
        chart_data: [
          { concept: 'Missing Values', strength: 90 },
          { concept: 'Duplicate Records', strength: 85 },
          { concept: 'Invalid Values', strength: 70 },
          { concept: 'Mixed Date Formats', strength: 40 },
          { concept: 'Typo Errors', strength: 75 },
        ],
      },
      next_steps: {
        can_retake: false,
        next_retake_available_at: null,
        can_level_up: true,
      },
    };

    setTimeout(() => {
      setResults(mockResults);
      setIsLoading(false);
    }, 1500);
  }, []);

  const getRankBadgeClass = (rank: string) => {
    switch (rank) {
      case 'beginner': return 'badge-beginner';
      case 'intermediate': return 'badge-intermediate';
      case 'advanced': return 'badge-advanced';
      case 'expert': return 'badge-expert';
      default: return 'badge-beginner';
    }
  };

  if (isLoading) {
    return (
      <div className="screen-container flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-3 border-[#FF6B2B] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-[#A0A2A8]">Calculating your results...</p>
        </div>
      </div>
    );
  }

  if (!results) return null;

  return (
    <div className="screen-container">
      <div className="max-w-2xl mx-auto w-full">
        {/* Pass/Fail Badge */}
        <div className="text-center mb-8">
          <div className={`w-24 h-24 mx-auto mb-4 rounded-full flex items-center justify-center ${
            results.overall_passed 
              ? 'bg-green-500/20 border-4 border-green-500' 
              : 'bg-red-500/20 border-4 border-red-500'
          }`}>
            {results.overall_passed ? (
              <svg className="w-12 h-12 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-12 h-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
          </div>
          
          <h1 className={`text-3xl font-bold mb-2 ${
            results.overall_passed ? 'text-green-400' : 'text-red-400'
          }`}>
            {results.overall_passed ? 'Congratulations!' : 'Not This Time'}
          </h1>
          
          <p className="text-[#A0A2A8]">
            {results.overall_passed 
              ? 'You passed the simulation and earned your rank.' 
              : 'You did not meet the pass threshold. Review and try again.'}
          </p>
        </div>

        {/* Score Cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="card text-center">
            <p className="text-sm text-[#6B6D75] mb-1">Knowledge</p>
            <p className={`text-2xl font-bold font-mono ${
              results.scores.knowledge.passed ? 'text-green-400' : 'text-red-400'
            }`}>
              {results.scores.knowledge.score}%
            </p>
            <p className="text-xs text-[#6B6D75]">68% weight</p>
          </div>
          
          <div className="card text-center">
            <p className="text-sm text-[#6B6D75] mb-1">Mini Task</p>
            <p className={`text-2xl font-bold font-mono ${
              results.scores.mini_task.passed ? 'text-green-400' : 'text-red-400'
            }`}>
              {results.scores.mini_task.score}%
            </p>
            <p className="text-xs text-[#6B6D75]">32% weight</p>
          </div>
          
          <div className="card text-center border-[#FF6B2B]/30">
            <p className="text-sm text-[#6B6D75] mb-1">Overall</p>
            <p className={`text-2xl font-bold font-mono ${
              results.overall_passed ? 'text-[#FF6B2B]' : 'text-red-400'
            }`}>
              {results.scores.overall.toFixed(1)}%
            </p>
            <p className="text-xs text-[#6B6D75]">Pass: 80%</p>
          </div>
        </div>

        {/* Rank Promotion */}
        {results.rank.promoted && (
          <div className="card mb-8 text-center">
            <p className="text-sm text-[#6B6D75] mb-2">Rank Achieved</p>
            <div className="flex items-center justify-center gap-4">
              <span className={`badge ${getRankBadgeClass(results.rank.previous)}`}>
                {results.rank.previous}
              </span>
              <span className="text-[#6B6D75]">→</span>
              <span className={`badge ${getRankBadgeClass(results.rank.new)}`}>
                {results.rank.new}
              </span>
            </div>
          </div>
        )}

        {/* Skill DNA */}
        <div className="card mb-8">
          <h3 className="font-semibold text-white mb-4">Your Skill DNA</h3>
          
          {/* Simple bar chart for skill strengths */}
          <div className="space-y-3">
            {results.skill_dna.chart_data.map((item) => (
              <div key={item.concept}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-[#A0A2A8]">{item.concept}</span>
                  <span className={`font-mono ${
                    item.strength >= 70 ? 'text-green-400' : 
                    item.strength < 40 ? 'text-red-400' : 'text-[#F5C842]'
                  }`}>
                    {item.strength}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-bar-fill"
                    style={{ 
                      width: `${item.strength}%`,
                      background: item.strength >= 70 
                        ? '#22C55E' 
                        : item.strength < 40 
                          ? '#EF4444' 
                          : 'linear-gradient(90deg, #FF6B2B, #F5C842)'
                    }} 
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Focus Areas */}
          {results.skill_dna.weaknesses.length > 0 && (
            <div className="mt-6 p-4 bg-[#1E1F24] rounded-lg">
              <p className="text-sm text-[#A0A2A8] mb-2">Recommended Focus Areas:</p>
              <div className="flex flex-wrap gap-2">
                {results.skill_dna.weaknesses.map((weakness) => (
                  <span key={weakness} className="badge badge-beginner">
                    {weakness.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={onBackToSkills}
            className="btn btn-secondary flex-1"
          >
            Back to Skills
          </button>
          
          {results.next_steps.can_level_up && (
            <button
              onClick={onBackToSkills}
              className="btn btn-primary flex-1"
            >
              Level Up
            </button>
          )}
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center">
          <p className="text-xs text-[#6B6D75]">
            Your Skill DNA updates after every simulation.
            <br />
            Focus on weak areas to improve faster.
          </p>
        </div>
      </div>
    </div>
  );
}
