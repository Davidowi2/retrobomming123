import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import type { User } from '../App';

interface SkillSelectionScreenProps {
  user: User;
  onStartSimulation: () => void;
}

interface JobType {
  job_type_id: string;
  name: string;
  description: string;
  avg_simulation_minutes: number;
  submission_type: string;
}

interface SkillHeader {
  header_id: string;
  name: string;
  description: string;
  icon_url?: string;
  job_types: JobType[];
}

interface UserSkill {
  id: string;
  job_type_id: string;
  job_type_name: string;
  current_rank: string;
  status: string;
  next_retake_available_at: string | null;
  total_attempts: number;
}

export function SkillSelectionScreen({ user, onStartSimulation }: SkillSelectionScreenProps) {
  const [headers, setHeaders] = useState<SkillHeader[]>([]);
  const [userSkills, setUserSkills] = useState<UserSkill[]>([]);
  const [selectedHeader, setSelectedHeader] = useState<SkillHeader | null>(null);
  const [selectedJobTypes, setSelectedJobTypes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'select' | 'my_skills'>('my_skills');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [headersData, skillsData] = await Promise.all([
        api.getSkillHeaders(),
        api.getUserSkills(),
      ]);
      setHeaders(headersData);
      setUserSkills(skillsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleJobTypeSelect = (jobTypeId: string) => {
    setSelectedJobTypes(prev => 
      prev.includes(jobTypeId)
        ? prev.filter(id => id !== jobTypeId)
        : [...prev, jobTypeId]
    );
  };

  const handleSaveSkills = async () => {
    if (selectedJobTypes.length === 0) return;
    
    setIsSaving(true);
    try {
      await api.addUserSkills(selectedJobTypes);
      await loadData();
      setSelectedJobTypes([]);
      setSelectedHeader(null);
      setActiveTab('my_skills');
    } catch (error) {
      console.error('Failed to save skills:', error);
    } finally {
      setIsSaving(false);
    }
  };

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
        <div className="animate-spin w-8 h-8 border-2 border-[#FF6B2B] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="screen-container">
      <div className="max-w-4xl mx-auto w-full">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome, {user.full_name.split(' ')[0]}
          </h1>
          <p className="text-[#A0A2A8]">
            Select your skills and take simulations to prove your abilities.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-[#1E1F24]">
          <button
            onClick={() => setActiveTab('my_skills')}
            className={`pb-3 text-sm font-medium transition-colors ${
              activeTab === 'my_skills'
                ? 'text-[#FF6B2B] border-b-2 border-[#FF6B2B]'
                : 'text-[#A0A2A8] hover:text-white'
            }`}
          >
            My Skills ({userSkills.length})
          </button>
          <button
            onClick={() => setActiveTab('select')}
            className={`pb-3 text-sm font-medium transition-colors ${
              activeTab === 'select'
                ? 'text-[#FF6B2B] border-b-2 border-[#FF6B2B]'
                : 'text-[#A0A2A8] hover:text-white'
            }`}
          >
            Add New Skills
          </button>
        </div>

        {/* My Skills Tab */}
        {activeTab === 'my_skills' && (
          <div className="space-y-4">
            {userSkills.length === 0 ? (
              <div className="card text-center py-12">
                <p className="text-[#A0A2A8] mb-4">You haven't selected any skills yet.</p>
                <button
                  onClick={() => setActiveTab('select')}
                  className="btn btn-primary"
                >
                  Select Your First Skill
                </button>
              </div>
            ) : (
              userSkills.map((skill) => (
                <div key={skill.id} className="card flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-white mb-1">{skill.job_type_name}</h3>
                    <div className="flex items-center gap-3">
                      <span className={`badge ${getRankBadgeClass(skill.current_rank)}`}>
                        {skill.current_rank}
                      </span>
                      <span className="text-sm text-[#6B6D75]">
                        {skill.total_attempts} attempt{skill.total_attempts !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    {skill.status === 'pending_simulation' ? (
                      <button
                        onClick={onStartSimulation}
                        className="btn btn-primary"
                      >
                        Start Simulation
                      </button>
                    ) : skill.next_retake_available_at ? (
                      <div className="text-right">
                        <p className="text-sm text-[#F59E0B]">Cooldown Active</p>
                        <p className="text-xs text-[#6B6D75]">
                          Available {new Date(skill.next_retake_available_at).toLocaleDateString()}
                        </p>
                      </div>
                    ) : (
                      <button
                        onClick={onStartSimulation}
                        className="btn btn-secondary"
                      >
                        Level Up
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Select Skills Tab */}
        {activeTab === 'select' && (
          <div className="space-y-6">
            {!selectedHeader ? (
              // Show headers
              headers.map((header) => (
                <div
                  key={header.header_id}
                  onClick={() => setSelectedHeader(header)}
                  className="card cursor-pointer hover:border-[#FF6B2B]/50"
                >
                  <h3 className="font-semibold text-white mb-2">{header.name}</h3>
                  <p className="text-sm text-[#A0A2A8] mb-3">{header.description}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#6B6D75]">
                      {header.job_types.length} job types
                    </span>
                    <span className="text-[#FF6B2B]">→</span>
                  </div>
                </div>
              ))
            ) : (
              // Show job types for selected header
              <div>
                <button
                  onClick={() => {
                    setSelectedHeader(null);
                    setSelectedJobTypes([]);
                  }}
                  className="text-sm text-[#A0A2A8] hover:text-white mb-4"
                >
                  ← Back to categories
                </button>
                
                <h2 className="text-xl font-bold text-white mb-2">{selectedHeader.name}</h2>
                <p className="text-[#A0A2A8] mb-6">{selectedHeader.description}</p>
                
                <div className="space-y-3 mb-6">
                  {selectedHeader.job_types.map((jobType) => (
                    <div
                      key={jobType.job_type_id}
                      onClick={() => handleJobTypeSelect(jobType.job_type_id)}
                      className={`card cursor-pointer transition-all ${
                        selectedJobTypes.includes(jobType.job_type_id)
                          ? 'border-[#FF6B2B] bg-[#FF6B2B]/10'
                          : 'hover:border-[#FF6B2B]/50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium text-white mb-1">{jobType.name}</h4>
                          <p className="text-sm text-[#A0A2A8]">{jobType.description}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-[#6B6D75]">
                            <span>~{jobType.avg_simulation_minutes} min</span>
                            <span>•</span>
                            <span>{jobType.submission_type.replace('_', ' ')}</span>
                          </div>
                        </div>
                        <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                          selectedJobTypes.includes(jobType.job_type_id)
                            ? 'border-[#FF6B2B] bg-[#FF6B2B]'
                            : 'border-[#6B6D75]'
                        }`}>
                          {selectedJobTypes.includes(jobType.job_type_id) && (
                            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {selectedJobTypes.length > 0 && (
                  <button
                    onClick={handleSaveSkills}
                    disabled={isSaving}
                    className="btn btn-primary w-full"
                  >
                    {isSaving ? (
                      <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    ) : (
                      `Add ${selectedJobTypes.length} Skill${selectedJobTypes.length !== 1 ? 's' : ''}`
                    )}
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
