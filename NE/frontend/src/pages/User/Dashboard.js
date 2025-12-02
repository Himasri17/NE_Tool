import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate} from "react-router-dom";
import {
    Container, Typography, TextField, Button, Box, List, ListItem, ListItemText,
    Paper, Dialog, DialogActions, DialogContent, Divider, ListItemIcon,
    DialogContentText, DialogTitle, Chip, CircularProgress, 
    Grid, LinearProgress, Card, CardContent ,FormControl, InputLabel, Select, MenuItem, useTheme, Alert,Tooltip,
    Drawer, IconButton, Badge 
} from "@mui/material";
import FeedbackIcon from '@mui/icons-material/Feedback'; 
import RateReviewIcon from '@mui/icons-material/RateReview';
import AssignmentLateIcon from '@mui/icons-material/AssignmentLate'
import MenuIcon from '@mui/icons-material/Menu';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import RuleIcon from '@mui/icons-material/Rule'; // User Guidelines
import DescriptionIcon from '@mui/icons-material/Description'; // Annotation Guidelines
import QueryStatsIcon from '@mui/icons-material/QueryStats'; // Tag Stats
import LogoutIcon from '@mui/icons-material/Logout'; // Logout Icon
import { getToken, removeToken } from '../../components/authUtils'; // <-- FIXED PATH


import FeedbackDialog from './FeedbackDialog'; // <-- FIXED PATH
import { SentencesRevisionNotesDialog } from './SentencesRevisionNotesDialog'; // <-- FIXED PATH

const API_BASE_URL = 'http://127.0.0.1:5001';


export default function Dashboard() {
    const { username } = useParams();
    const navigate = useNavigate();
    const theme = useTheme();

    // --- State Management ---
    const [userData, setUserData] = useState(null);
    const [projectTasks, setProjectTasks] = useState([]);
    const [allSentences, setAllSentences] = useState([]);
    const [visibleSentences, setVisibleSentences] = useState([]);
    const [tags, setTags] = useState([]);
    const [selectedSentence, setSelectedSentence] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [autoTags, setAutoTags] = useState([]);
    const [newSelection, setNewSelection] = useState({ isActive: false, text: '', tag: '' });
    const [editingSentence, setEditingSentence] = useState({ isActive: false, _id: null, textContent: '' });
    const [editingTag, setEditingTag] = useState({ isActive: false, _id: null, text: '', tag: '' });
    const [deleteConfirmation, setDeleteConfirmation] = useState({ isOpen: false, sentenceId: null });
    const [bulkUploadDialog, setBulkUploadDialog] = useState(false);
    const [file, setFile] = useState(null);
    const [tagReviewStatus, setTagReviewStatus] = useState({});
    const [bulkTag, setBulkTag] = useState('');
    const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
    const [tagRecommendations, setTagRecommendations] = useState([]);
    const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
    const [showRecommendations, setShowRecommendations] = useState(false);
    const [statsDialogOpen, setStatsDialogOpen] = useState(false);
    const [tagStats, setTagStats] = useState(null);
    const [isLoadingStats, setIsLoadingStats] = useState(false);
    
    // FIXED: Use state for currentSentenceTags instead of derived value
    const [currentSentenceTags, setCurrentSentenceTags] = useState([]);

    const [revisionList, setRevisionList] = useState([]);
    const [isRevisionNotesDialogOpen, setIsRevisionNotesDialogOpen] = useState(false);
    const [drawerOpen, setDrawerOpen] = useState(false); // <-- NEW DRAWER STATE


    const [reviewStatusMessage, setReviewStatusMessage] = useState(null);

    // --- SEARCH & TAG MATCH STATES ---
    const [searchTerm, setSearchTerm] = useState('');
    const [matchedTag, setMatchedTag] = useState(null);
    

    const TAG_STRUCTURE = {
    "TIMEX": ["Time", "Date", "Day"],
    "NUMEX": ["Currency", "Measurement", "Cardinal"],
    "ENAMEX": ["Person", "Organisation", "Location", "Facilities", "Artifacts"],
    };
    
    const HIERARCHICAL_TAGS = Object.entries(TAG_STRUCTURE).flatMap(([mainTag, subtypes]) =>
        subtypes.map(subtype => `${mainTag}_${subtype}`)
    );
    const PREDEFINED_TAGS = [
            "Noun Compound",
            "Reduplicated", 
            "Echo",
            "Opaque",
            "Opaque-Idiom"
    ];

    // --- PROJECT STATES ---
    const [selectedProject, setSelectedProject] = useState(null); 
    const [projectName, setProjectName] = useState(""); 

    // --- Ref for scroll control ---
    const listRef = useRef(null);
    const isInitialLoad = useRef(true);

    useEffect(() => {
        const token = getToken();
        if (!token) {
            navigate("/");
            return;
        }
    }, [navigate]);

    const fetchWithAuth = async (url, options = {}) => {
        const token = getToken();
        
        // For logout endpoint, always try to send the request even with expired token
        const isLogoutEndpoint = url.includes('/logout');
        
        if (!token && !isLogoutEndpoint) {
            removeToken();
            navigate("/");
            return null;
        }

        const headers = {
            ...options.headers,
        };
        
        // Only add Authorization header if we have a token
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            // For logout, we don't care about 401 responses
            if (response.status === 401 && !isLogoutEndpoint) {
                removeToken();
                navigate("/");
                return null;
            }

            return response;
        } catch (error) {
            // For logout endpoint, don't navigate away on network errors
            if (!isLogoutEndpoint) {
                // removeToken(); // Don't remove token immediately on network error, only on 401
                // navigate("/");
            }
            return null;
        }
    };

    const handleNavigateToSentence = async (sentenceId) => {
        try {
            // Find the sentence in all sentences
            const targetSentence = allSentences.find(s => s._id === sentenceId);
            
            if (targetSentence) {
                // Select the sentence
                setSelectedSentence(targetSentence);
                
                // If the sentence is in a different project, switch to that project
                if (targetSentence.project_id && selectedProject?.project_name !== targetSentence.project_id) {
                    const targetProject = projectTasks.find(p => 
                        p.sentences.some(s => s._id === sentenceId)
                    );
                    if (targetProject) {
                        handleSelectProject(targetProject);
                    }
                }
                
                // Scroll to the sentence in the list
                setTimeout(() => {
                    const sentenceElement = document.querySelector(`[data-sentence-id="${sentenceId}"]`);
                    if (sentenceElement) {
                        sentenceElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        
                        // Highlight the sentence temporarily
                        sentenceElement.style.backgroundColor = '#fff3e0';
                        setTimeout(() => {
                            sentenceElement.style.backgroundColor = '';
                        }, 2000);
                    }
                }, 100);
                
                console.log(`Mapsd to sentence: ${sentenceId}`);
            } else {
                console.warn(`Sentence ${sentenceId} not found in current view`);
                alert('Sentence not found in current project. Please check the project selection.');
            }
        } catch (error) {
            console.error('Error navigating to sentence:', error);
            alert('Error navigating to sentence. Please try manually finding it in the list.');
        }
    };
    const isHierarchicalTag = (tag) => {
    return HIERARCHICAL_TAGS.includes(tag);
    };


    useEffect(() => {
        const fetchRevisionNotesCount = async () => {
            if (!username) return;
            
            try {
                console.log("DEBUG: Fetching revision notes for user:", username);
                const response = await fetchWithAuth(`${API_BASE_URL}/api/annotator/revision_notes/${username}`, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response && response.ok) {
                    const notes = await response.json();
                    console.log("DEBUG: Received revision notes:", notes);
                    console.log("DEBUG: Number of revision notes:", notes.length);
                    setRevisionList(notes);
                } else if (response) {
                    console.error('Failed to fetch revision notes:', response.status);
                }
            } catch (error) {
                console.error('Error fetching revision notes count:', error);
            }
        };

        fetchRevisionNotesCount();
        const interval = setInterval(fetchRevisionNotesCount, 30000);
        return () => clearInterval(interval);
    }, [username]);

    const fetchTags = useCallback(async () => {
        try {
            console.log("DEBUG: Starting to fetch tags for user:", username);
            const res = await fetchWithAuth(`http://127.0.0.1:5001/tags/${username}`);
            if (!res) return; // Authentication failed
            
            if (!res.ok) throw new Error("Failed to fetch tags");
            
            const tagsData = await res.json();
            console.log("DEBUG: Tags fetched from server:", tagsData);
            console.log("DEBUG: Number of tags received:", tagsData.length);
            
            setTags(tagsData);
        } catch (err) { 
            console.error("Error fetching tags:", err); 
        }
    }, [username]);

    useEffect(() => {
        if (selectedSentence && tags.length > 0) {
            const filteredTags = tags.filter(tag => {
                const matches = tag.source_sentence_id === selectedSentence._id;
                console.log(`Filtering tag ${tag._id} for sentence ${selectedSentence._id}: ${matches}`);
                return matches;
            });
            console.log("Setting currentSentenceTags to:", filteredTags);
            setCurrentSentenceTags(filteredTags);
        } else {
            console.log("Clearing currentSentenceTags");
            setCurrentSentenceTags([]);
        }
    }, [selectedSentence, tags]);

    const loadAllUserTasks = useCallback(async (setLoading = true, preserveCurrentProject = false) => {
    if (setLoading) setIsLoading(true);
    try {
        const res = await fetchWithAuth(`http://127.0.0.1:5001/sentences/${username}`);
        if (!res) return; // Authentication failed
        
        if (!res.ok) throw new Error("Failed to fetch all user tasks.");
        const data = await res.json();
        
        const projects = data.project_tasks || [];
        setProjectTasks(projects);
        
        let initialProject = null;
        
        // If we want to preserve the current project, use the existing selectedProject
        if (preserveCurrentProject && selectedProject) {
            // Find the updated version of the current project
            const currentProjectInList = projects.find(p => p.project_name === selectedProject.project_name);
            if (currentProjectInList) {
                initialProject = currentProjectInList;
            }
        }
        
        // If no current project to preserve or it wasn't found, use the original logic
        if (!initialProject && projects.length > 0) {
            initialProject = projects.find(p => p.completed < p.total);
            if (!initialProject) {
                initialProject = projects[0]; 
            }
        }

        // Set initial visibility based on selection
        if (initialProject) {
            setSelectedProject(initialProject);
            setProjectName(initialProject.project_name);
            setAllSentences(initialProject.sentences || []);
        } else {
            setSelectedProject(null);
            setProjectName(projects.length > 0 ? "No Unfinished Tasks Selected" : "No Assigned Projects");
            setAllSentences([]); 
            setVisibleSentences([]); 
        }
        
        // Only clear selected sentence if we're switching projects
        if (!preserveCurrentProject || !selectedProject) {
            setSelectedSentence(null); 
        }
        setSearchTerm(''); 
        
    } catch (err) { 
        console.error("Error loading user tasks:", err); 
        setProjectTasks([]);
        setAllSentences([]);
        setVisibleSentences([]);
    } finally {
        if (setLoading) setIsLoading(false);
    }
}, [username]); // REMOVE selectedProject from dependencies

    useEffect(() => {
        const loadData = async () => {
            await fetchTags();
            await loadAllUserTasks();
        };
        loadData();
    }, [fetchTags, loadAllUserTasks]);

    useEffect(() => {
        // Close recommendations when selecting a different sentence
        if (!selectedSentence) {
            setShowRecommendations(false);
            setTagRecommendations([]);
        }
    }, [selectedSentence]);

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                const res = await fetchWithAuth(`http://127.0.0.1:5001/api/user/${username}`);
                if (res && res.ok) {
                    const data = await res.json();
                    setUserData(data);
                }
            } catch (err) {
                console.error("Error fetching user data:", err);
            }
        };
        
        if (username) {
            fetchUserData();
        }
    }, [username]);

    // --- UPDATED: Search Filtering Effect (Handles Sentence and Tag Match) ---
    useEffect(() => {
        const normalizedSearchTerm = searchTerm.toLowerCase().trim();

        if (normalizedSearchTerm === '') {
            setVisibleSentences(allSentences);
            setMatchedTag(null); 
            return;
        }

        // 1. Find if the search term matches any tag (text or label) globally
        const foundTag = tags.find(tag => 
            tag.text.toLowerCase() === normalizedSearchTerm || 
            tag.tag.toLowerCase() === normalizedSearchTerm
        );
        
        setMatchedTag(foundTag || null);
        setSelectedSentence(null); // Clear selected sentence when a search is active

        // 2. Filter sentences based on content or associated tag
        const filtered = allSentences.filter(sentence => {
            const textMatch = sentence.textContent.toLowerCase().includes(normalizedSearchTerm);

            const sentenceTags = tags.filter(t => t.source_sentence_id === sentence._id);
            const tagMatch = sentenceTags.some(tag => 
                tag.text.toLowerCase().includes(normalizedSearchTerm) || 
                tag.tag.toLowerCase().includes(normalizedSearchTerm)
            );
            
            return textMatch || tagMatch;
        });

        setVisibleSentences(filtered);
    }, [searchTerm, allSentences, tags]);
    
    // Scroll to first unannotated sentence only on initial load
    useEffect(() => {
        if (isLoading || visibleSentences.length === 0 || !listRef.current || !isInitialLoad.current || searchTerm.length > 0) return;

        const firstUnannotatedIndex = visibleSentences.findIndex(s => !s.is_annotated);
        if (firstUnannotatedIndex !== -1) {
            const targetElement = listRef.current.children[firstUnannotatedIndex];
            if (targetElement) {
                const listContainer = listRef.current;
                const offsetTop = targetElement.offsetTop;
                listContainer.scrollTop = offsetTop;
            }
        }
        isInitialLoad.current = false;
    }, [isLoading, visibleSentences, searchTerm]);
    
    useEffect(() => {
        console.log("DEBUG: Auto-tag detection running", {
            selectedSentence: selectedSentence?.textContent,
            currentSentenceTags: currentSentenceTags,
            newSelectionActive: newSelection.isActive
        });

        if (!selectedSentence || currentSentenceTags.length === 0) {
            console.log("DEBUG: No selected sentence or no current tags");
            setAutoTags([]);
            return;
        }
        
        const uniqueTagTexts = [...new Set(currentSentenceTags.map(t => t.text.toLowerCase()))];
        const foundTags = [];
        
        console.log("DEBUG: Unique tag texts to check:", uniqueTagTexts);
        
        uniqueTagTexts.forEach(tagText => {
            const regex = new RegExp(`\\b${tagText}\\b`, 'i');
            if (regex.test(selectedSentence.textContent)) {
                console.log("DEBUG: Found matching tag in sentence:", tagText);
                const originalTag = currentSentenceTags.find(t => t.text.toLowerCase() === tagText);
                if (originalTag) {
                    foundTags.push({ 
                        phrase: originalTag.text,
                        recommended_tag: originalTag.tag,
                        confidence: 0.95,
                        occurrence_count: 1,
                        is_auto_detected: true
                    });
                }
            }
        });
        
        console.log("DEBUG: Found auto-detected tags:", foundTags);
        
        // ONLY set as recommendations, don't auto-apply
        if (foundTags.length > 0) {
            console.log("DEBUG: Setting auto-detected tags as recommendations only");
            setTagRecommendations(prev => {
                // Keep API recommendations and add auto-detected ones
                const apiRecs = prev.filter(rec => !rec.is_auto_detected);
                return [...foundTags, ...apiRecs];
            });
        }
    }, [selectedSentence, currentSentenceTags]);

    const logUserAction = async (description) => {
    try {
        await fetchWithAuth('http://127.0.0.1:5001/api/log-action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                description: description
            })
        });
    } catch (error) {
        console.error('Failed to log action:', error);
    }
};

    const fetchTagRecommendations = async (text) => {
        if (!text || text.trim().length < 2) {
            // Don't clear auto-detected tags, only clear API recommendations
            setTagRecommendations(prev => prev.filter(rec => rec.is_auto_detected));
            return;
        }

        setIsLoadingRecommendations(true);
        try {
            const response = await fetchWithAuth('http://127.0.0.1:5001/api/recommend-tags/text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            if (!response) return; // Authentication failed

            if (response.ok) {
                const data = await response.json();
                // Merge API recommendations with existing auto-detected tags
                const apiRecommendations = data.recommendations || [];
                setTagRecommendations(prev => {
                    const autoDetected = prev.filter(rec => rec.is_auto_detected);
                    return [...autoDetected, ...apiRecommendations];
                });
                setShowRecommendations(true);
            } else {
                console.error('Failed to fetch recommendations');
                // Keep auto-detected tags even if API fails
                setTagRecommendations(prev => prev.filter(rec => rec.is_auto_detected));
            }
        } catch (error) {
            console.error('Error fetching recommendations:', error);
            // Keep auto-detected tags even if API fails
            setTagRecommendations(prev => prev.filter(rec => rec.is_auto_detected));
        } finally {
            setIsLoadingRecommendations(false);
        }
    };


    // --- Event Handlers ---
    
    const handleSearchChange = (event) => {
        setSearchTerm(event.target.value);
    };

      const handleOpenStats = async () => {
        setIsLoadingStats(true);
        setStatsDialogOpen(true);
        
        try {
            const response = await fetchWithAuth('http://127.0.0.1:5001/api/recommendation-stats');
            if (!response) return; // Authentication failed
            
            if (response.ok) {
                const stats = await response.json();
                setTagStats(stats);
            } else {
                console.error('Failed to fetch tag stats');
                setTagStats(null);
            }
        } catch (error) {
            console.error('Error fetching tag stats:', error);
            setTagStats(null);
        } finally {
            setIsLoadingStats(false);
        }
    };

    const handleSelectProject = (project) => {
    setSelectedProject(project);
    setSelectedSentence(null);
    setNewSelection({ isActive: false, text: '', tag: '' });
    setEditingTag({ isActive: false, _id: null, text: '', tag: '' });
    setSearchTerm(''); // Clear search on project switch
    setMatchedTag(null); // Clear tag match on project switch
    isInitialLoad.current = true; // Reset for new project
    
    // Log project selection
    if (project) {
        logUserAction(`Selected project: "${project.project_name}"`);
    } else {
        logUserAction('Deselected project');
    }
    
    if (project === null) {
        setAllSentences([]);
        setVisibleSentences([]);
        setProjectName("No Project Selected");
    } else {
        const fullProject = projectTasks.find(p => p.project_name === project.project_name);
        if (fullProject) {
            setAllSentences(fullProject.sentences);
            setVisibleSentences(fullProject.sentences);
            setProjectName(fullProject.project_name);
        }
    }
};  

    const handleSelectionEvent = (sentence) => {
    const highlightedText = window.getSelection().toString().trim();
    setSelectedSentence(sentence);
    setEditingTag({ isActive: false, _id: null, text: '', tag: '' });

    // Log sentence selection
    logUserAction(`Selected sentence for annotation`);

    // ✅ Only trigger tag creation if user actually highlighted text (not just clicked)
    if (!highlightedText || window.getSelection().type !== "Range") {
        setNewSelection({ isActive: false, text: '', tag: '' });
        setTagRecommendations([]);
        setShowRecommendations(false);
        return;
    }

    // If actual text is selected, continue with tag suggestion logic
    if (highlightedText.length > 0 && !editingSentence.isActive) {
        let suggestion = "Noun Compound";
        const lowerCaseText = highlightedText.toLowerCase();
        const existingTag = tags.find(t => t.text.toLowerCase() === lowerCaseText);

        if (existingTag) {
            suggestion = existingTag.tag;
        }

        setNewSelection({ isActive: true, text: highlightedText, tag: suggestion });

        // Immediately check for auto-detected tags from current sentence
        const autoDetectedTags = findAutoDetectedTags(sentence, highlightedText);
        if (autoDetectedTags.length > 0) {
            setTagRecommendations(autoDetectedTags);
            setShowRecommendations(true);
        }

        // Then fetch API recommendations
        fetchTagRecommendations(highlightedText);
    } else {
        setNewSelection({ isActive: false, text: '', tag: '' });
        setTagRecommendations([]);
        setShowRecommendations(false);
    }
};


    // Add this helper function
    const findAutoDetectedTags = (sentence, highlightedText) => {
        if (!sentence || !currentSentenceTags.length) return [];
        
        const uniqueTagTexts = [...new Set(currentSentenceTags.map(t => t.text.toLowerCase()))];
        const foundTags = [];
        
        uniqueTagTexts.forEach(tagText => {
            const regex = new RegExp(`\\b${tagText}\\b`, 'i');
            if (regex.test(sentence.textContent)) {
                const originalTag = currentSentenceTags.find(t => t.text.toLowerCase() === tagText);
                if (originalTag) {
                    foundTags.push({ 
                        phrase: originalTag.text,
                        recommended_tag: originalTag.tag,
                        confidence: 0.95,
                        occurrence_count: 1,
                        is_auto_detected: true
                    });
                }
            }
        });
        
        return foundTags;
    };

    const handleSelectRecommendation = (recommendation) => {
    setNewSelection(prev => ({
        ...prev,
        tag: recommendation.recommended_tag
    }));
    setShowRecommendations(false);
    
    // Log recommendation selection
    logUserAction(`Selected recommended tag: "${recommendation.recommended_tag}" for phrase: "${recommendation.phrase}"`);
};


   const handleSaveNewTag = async () => {
    if (!selectedSentence || !newSelection.text.trim() || !newSelection.tag.trim()) {
        return alert("Please provide both text and a tag label.");
    }

    const tagData = {
        username,
        text: newSelection.text.trim(),
        tag: newSelection.tag.trim(),
        sentenceId: selectedSentence._id
        // ❌ Removed review_status and status
    };

    console.log("DEBUG: Sending tag data:", tagData);

    const response = await fetchWithAuth(`http://127.0.0.1:5001/tags`, {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tagData),
    });

    if (!response) return;

    if (!response.ok) {
        const errorText = await response.text();
        console.error("DEBUG: Failed to create tag:", errorText);
        alert('Failed to create tag. Please try again.');
        return;
    }

    const result = await response.json();
    console.log("DEBUG: Tag creation response:", result);

    await logUserAction(`Added tag: "${newSelection.text.trim()}" as "${newSelection.tag.trim()}"`);

    await fetchTags();
    
    setNewSelection({ isActive: false, text: '', tag: '' });
    setSelectedSentence(prev => ({ ...prev }));
};

    const handleRemoveTag = async (tagId) => {
    if (!selectedSentence) return;
    
    // Get tag info before deletion for logging
    const tagToRemove = currentSentenceTags.find(tag => tag._id === tagId);
    
    const response = await fetchWithAuth(`http://127.0.0.1:5001/api/tags/${tagId}`, { 
        method: 'DELETE' 
    });
    
    if (!response) return; // Authentication failed
    
    if (response.ok) {
        // Log the tag removal action
        if (tagToRemove) {
            await logUserAction(`Removed tag: "${tagToRemove.text}" (${tagToRemove.tag}) from sentence`);
        }
        
        await fetchTags();
    } else {
        console.error('Failed to remove tag');
        alert('Failed to remove tag. Please try again.');
    }
};


    const handleStartEditTag = (tag) => {
    // No need to check for hierarchical tags here since they won't be clickable
    setEditingTag({ isActive: true, _id: tag._id, text: tag.text, tag: tag.tag });
    setNewSelection({ isActive: false, text: '', tag: '' });
};
    
    // Update the handleUpdateTag function
const handleUpdateTag = async () => {
    if (!editingTag._id) return;

    // Local update for snappier UI
    setTags(prevTags =>
        prevTags.map(tag =>
            tag._id === editingTag._id
                ? { ...tag, text: editingTag.text, tag: editingTag.tag }
                : tag
        )
    );

    try {
        const response = await fetchWithAuth(`http://127.0.0.1:5001/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                text: editingTag.text.trim(),
                tag: editingTag.tag.trim(),
                sentenceId: selectedSentence._id 
            })
        });
        
        if (!response) return; // Authentication failed
        
        // Log the tag update action
        await logUserAction(`Updated tag to: "${editingTag.text.trim()}" as "${editingTag.tag.trim()}"`);
        
    } catch (err) {
        console.error("Error updating tag:", err);
    }

    setEditingTag({ isActive: false, _id: null, text: '', tag: '' });
};

const handleStatusChange = async (isAnnotated) => {
    if (!selectedSentence) return;

    // Optimistic UI Update - update local state only
    const updatedAllSentences = allSentences.map(s =>
        s._id === selectedSentence._id ? { ...s, is_annotated: isAnnotated } : s
    );
    setAllSentences(updatedAllSentences);
    setSelectedSentence({ ...selectedSentence, is_annotated: isAnnotated });

    // Also update projectTasks to reflect the change
    if (selectedProject) {
        const updatedProjectTasks = projectTasks.map(project => {
            if (project.project_name === selectedProject.project_name) {
                const updatedSentences = project.sentences.map(s =>
                    s._id === selectedSentence._id ? { ...s, is_annotated: isAnnotated } : s
                );
                
                // Recalculate completed count
                const completedCount = updatedSentences.filter(s => s.is_annotated).length;
                
                return {
                    ...project,
                    sentences: updatedSentences,
                    completed: completedCount
                };
            }
            return project;
        });
        
        setProjectTasks(updatedProjectTasks);
        
        // Update selectedProject as well
        const updatedSelectedProject = updatedProjectTasks.find(p => p.project_name === selectedProject.project_name);
        if (updatedSelectedProject) {
            setSelectedProject(updatedSelectedProject);
        }
    }

    try {
        const response = await fetchWithAuth(`http://127.0.0.1:5001/sentences/${selectedSentence._id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_annotated: isAnnotated, username }),
        });

        if (!response) return; // Authentication failed

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({ error: 'No JSON body available' }));
            console.error(`Status Update Failed: ${response.status}`, errorBody);
            throw new Error(errorBody.error || `Server Error (${response.status})`);
        }
        
        // Log the status change action
        await logUserAction(`Marked sentence as ${isAnnotated ? 'annotated' : 'not annotated'}`);
        

    } catch (err) {
        console.error("Final Error in Status Update:", err);
        alert(`Failed to update status. Reason: ${err.message}. Check console.`);
        
        // Revert local changes on error
        await loadAllUserTasks(false); // Only reload on error
    }
};
    

    const handleSubmitTagForReview = async (tagId) => {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/api/tag/${tagId}/submit_for_review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        if (!response) return;

        if (response.ok) {
            // Update local state to reflect the change
            setTagReviewStatus(prev => ({
                ...prev,
                [tagId]: 'pending'
            }));
            
            // Refresh tags to get updated data
            await fetchTags();
            
            // Log the action
            await logUserAction(`Submitted individual tag for review`);
            
            alert('Tag submitted for review successfully!');
        } else {
            const errorData = await response.json();
            alert(`Failed to submit tag for review: ${errorData.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error submitting tag for review:', error);
        alert('Error submitting tag for review. Please try again.');
    }
};

const handleCancelTagReview = async (tagId) => {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/api/tag/${tagId}/cancel_review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        if (!response) return;

        if (response.ok) {
            // Update local state
            setTagReviewStatus(prev => ({
                ...prev,
                [tagId]: 'approved'
            }));
            
            // Refresh tags
            await fetchTags();
            
            // Log the action
            await logUserAction(`Cancelled review request for tag`);
            
            alert('Tag review request cancelled successfully!');
        } else {
            const errorData = await response.json();
            alert(`Failed to cancel tag review: ${errorData.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error cancelling tag review:', error);
        alert('Error cancelling tag review. Please try again.');
    }
};

const getTagStatus = (tag) => {
    console.log("DEBUG: Checking tag status for:", tag._id, tag);
    
    // Check review_status first
    if (tag.review_status === 'Pending' || tag.review_status === 'pending') {
        return 'pending';
    } else if (tag.review_status === 'Approved' || tag.review_status === 'approved') {
        return 'approved';
    } else if (tag.review_status === 'Rejected' || tag.review_status === 'rejected') {
        return 'rejected';
    }
    
    // Fallback to status field
    if (tag.status === 'pending') {
        return 'pending';
    } else if (tag.status === 'approved') {
        return 'approved';
    }
    
    // Default for new tags should be approved
    return 'approved';
};

    const handleLogout = async () => {
        try {
            // Try to call logout API, but don't fail if it doesn't work
            await fetchWithAuth('http://127.0.0.1:5001/logout', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username }),
            }).catch(error => {
                console.warn("Logout API call failed, continuing with client-side logout:", error);
            });
        } catch (error) {
            console.warn("Logout API error, continuing with client-side logout:", error);
        } finally {
            // Always remove token and navigate to login
            removeToken();
            isInitialLoad.current = true;
            navigate("/login"); 
        }
    };

    const handleFeedbackClose = (success = false) => {
        setIsFeedbackOpen(false);
        if (success) {
            console.log("Feedback submission acknowledged.");
        }
    };

    // --- Counters ---
    const totalSentences = allSentences.length;
    const annotatedCount = allSentences.filter(s => s.is_annotated).length;
    const remainingCount = totalSentences - annotatedCount;
    const progressPercent = totalSentences > 0 ? Math.round((annotatedCount / totalSentences) * 100) : 0;
    
    const getProjectCardColor = (isPending) => isPending ? '#ffcdd2' : '#c8e6c9';

    // --- NEW: Handle Navigation from Drawer ---
    const handleDrawerNavigation = (path, action) => {
        setDrawerOpen(false);
        if (path) {
            navigate(path);
        } else if (action) {
            action();
        }
    };
    
    // --- NEW: Navigation Item List ---
    const navItems = [
        { name: 'User Guidelines', action: () => window.open('/NE Tool - User Guidelines.pdf', '_blank'), icon: RuleIcon, path: null },
        { name: 'Annotation Guidelines', action: () => window.open('/ne_Guidelines.pdf', '_blank'), icon: DescriptionIcon, path: null },
        { name: 'Give Feedback', action: () => setIsFeedbackOpen(true), icon: FeedbackIcon, path: null },
        { name: 'Revision Notes', action: () => setIsRevisionNotesDialogOpen(true), icon: AssignmentLateIcon, path: null, badge: revisionList.length },
        { name: 'Tag Statistics', action: handleOpenStats, icon: QueryStatsIcon, path: null },
    ];


    // --- Main Render ---

    return (
        
        <Container maxWidth="l" sx={{ overflow: 'hidden', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* --- NEW: HAMBURGER NAVBAR --- */}
            <Box 
                sx={{ 
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
                    height: '60px', bgcolor: theme.palette.primary.main, color: 'white', 
                    p: 2, width: '100%', boxSizing: 'border-box', flexShrink: 0 
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <IconButton
                        color="inherit" 
                        aria-label="open drawer"
                        onClick={() => setDrawerOpen(true)} 
                        edge="start"
                        sx={{ mr: 2 }}
                    >
                        <Badge badgeContent={revisionList.length} color="error" overlap="circular" max={99}>
                            <MenuIcon /> 
                        </Badge>
                    </IconButton>
                    <Typography variant="h6" fontWeight={500}>
                    NE Annotator - {userData?.full_name || userData?.username || username || "User"}
                    </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Button
                    color="inherit"
                    onClick={handleLogout}
                    startIcon={<LogoutIcon />}
                    sx={{ 
                        ml: 1,
                        '&:hover': {
                            backgroundColor: 'rgba(255, 255, 255, 0.1)'
                        }
                    }}
                >
                    Logout
                </Button>
            </Box>
                
                {/* --- DRAWER (HAMBURGER MENU) --- */}
                <Drawer
                    anchor="left" 
                    open={drawerOpen}
                    onClose={() => setDrawerOpen(false)}
                    PaperProps={{
                        sx: { width: 280, bgcolor: theme.palette.background.paper }
                    }}
                >
                    <Box sx={{ p: 2, bgcolor: theme.palette.primary.main, color: 'white', mb: 1 }}>
                        <Typography variant="h6" fontWeight="bold">User Menu</Typography>
                        <Typography variant="subtitle2">{username}</Typography>
                    </Box>
                    <Divider />
                    <List>
                        {navItems.map((item) => (
                            <ListItem 
                                key={item.name} 
                                button 
                                onClick={() => handleDrawerNavigation(item.path, item.action)}
                            >
                                <ListItemIcon>
                                    <Badge 
                                        badgeContent={item.badge || 0} 
                                        color={item.name === 'Revision Notes' ? 'error' : 'default'} 
                                        overlap="circular" max={99}
                                    >
                                        <item.icon color="primary" />
                                    </Badge>
                                </ListItemIcon>
                                <ListItemText primary={item.name} />
                            </ListItem>
                        ))}
                    </List>
                </Drawer>
            </Box>
            {/* --- END: NEW HAMBURGER NAVBAR --- */}

            <Paper elevation={3} sx={{ p: 4, mt: 4, mb: 4, maxHeight: '90vh', overflow: 'hidden' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h4" gutterBottom sx={{ mb: 0 }}>Welcome, {userData?.full_name || username || "User"}</Typography>
                </Box>
                
                {/* --- Project Selector --- */}
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h6" gutterBottom>Assigned Tasks</Typography>
                    <Grid container spacing={2}>
                        {projectTasks.length === 0 ? (
                                <Grid item xs={12}>
                                    <Typography color="text.secondary" sx={{ p: 2 }}>
                                        You have no assigned projects. Please contact your administrator.
                                    </Typography>
                                </Grid>
                        ) : (
                            projectTasks.map(project => {
                                const isPending = project.completed < project.total;
                                const progress = project.total > 0 ? Math.round((project.completed / project.total) * 100) : 0;

                                return (
                                    <Grid item xs={12} sm={6} md={3} key={project.project_name}>
                                        <Card 
                                            onClick={() => handleSelectProject(project)} 
                                            sx={{ 
                                                cursor: 'pointer', 
                                                border: selectedProject?.project_name === project.project_name ? '2px solid #1976d2' : '1px solid #ddd',
                                                backgroundColor: getProjectCardColor(isPending),
                                                height: '100%',
                                            }}
                                        >
                                            <CardContent sx={{ p: 1.5 }}>
                                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                                                    <FolderOpenIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                                                    {project.project_name}
                                                </Typography>
                                                <Typography variant="caption" display="block" color="text.secondary">
                                                    {project.completed}/{project.total} done
                                                </Typography>
                                                <LinearProgress 
                                                    variant="determinate" 
                                                    value={progress} 
                                                    sx={{ height: 6, borderRadius: 5, mt: 0.5 }} 
                                                    color={progress === 100 ? 'success' : 'primary'}
                                                />
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                )
                            })
                        )}
                    </Grid>
                </Box>

                {/* --- SEARCH BAR INTEGRATION --- */}
                <Box sx={{ mb: 3 }}>
                    <TextField
                        fullWidth
                        label="Search Sentence Content or Tags (e.g., 'heart', 'Action/Verb')"
                        variant="outlined"
                        value={searchTerm}
                        onChange={handleSearchChange}
                    />
                </Box>
            
                <Box sx={{ display: 'flex', gap: 3, mt: 2 }}>
                    <Box sx={{ width: '45%', display: 'flex', flexDirection: 'column', maxHeight: '100%' }}>
                        <Typography variant="h6" gutterBottom>Subject knowledge Sentences</Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="subtitle2">Total: {totalSentences}</Typography>
                            <Typography variant="subtitle2" color="success.main">Annotated: {annotatedCount}</Typography>
                            <Typography variant="subtitle2" color="error.main">Remaining: {remainingCount}</Typography>
                            <Typography variant="subtitle2">Progress: {progressPercent}%</Typography>
                        </Box>
                        <List
                            ref={listRef}
                            sx={{
                                maxHeight: '50vh',
                                overflowY: 'auto',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                p: 1
                            }}
                        >
                            {isLoading ? (
                                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                    <CircularProgress />
                                </Box>
                            ) : visibleSentences.length === 0 && totalSentences > 0 ? (
                                <Box sx={{ p: 2 }}>
                                    <Typography color="text.secondary">No sentences match your search term.</Typography>
                                </Box>
                            ) : totalSentences === 0 ? (
                                <Box sx={{ p: 2 }}>
                                    <Typography color="text.secondary">Select a project to view tasks, or contact your admin if no projects are shown above.</Typography>
                                </Box>
                            ) : (
                                visibleSentences.map((s) => (
                                    <ListItem
                                        key={s._id} divider button data-sentence-id={s._id} 
                                        selected={selectedSentence && selectedSentence._id === s._id}
                                        onMouseUp={() => handleSelectionEvent(s)}
                                        sx={{
                                            opacity: s.is_annotated ? 0.6 : 1,
                                            borderRadius: '4px', mb: 0.5,
                                            '&:hover .sentence-actions': { visibility: 'visible' }
                                        }}
                                    >
                                        <ListItemText
                                            primary={`${allSentences.findIndex(item => item._id === s._id) + 1}. ${s.textContent}`}
                                            primaryTypographyProps={{ sx: { fontStyle: s.is_annotated ? 'italic' : 'normal' } }}
                                        />
                                        <Box className="sentence-actions" sx={{ visibility: 'hidden', ml: 1, flexShrink: 0 }}>
                                            {/* Delete button removed */}
                                        </Box>
                                    </ListItem>
                                ))
                            )}
                        </List>
                    </Box>
                    <Box sx={{ width: '55%', display: 'flex', flexDirection: 'column', maxHeight: '100%' }}>
                        <Typography variant="h6" gutterBottom>Editor</Typography>
                        <Box sx={{ flexGrow: 1, border: '1px solid #ddd', borderRadius: '4px', p: 2, overflowY: 'auto' }}>
                            
                            {/* --- MODIFIED: SIMPLIFIED TAG DETAILS (Search Match) --- */}
                            {matchedTag && !selectedSentence ? (
                                <Box>
                                    <Box sx={{ p: 2, border: '1px solid #ddd', borderRadius: '4px', backgroundColor: '#e3f2fd' }}> 
                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Text: {matchedTag.text}</Typography>
                                        <Typography variant="subtitle2" color="primary">Label: {matchedTag.tag}</Typography>
                                    </Box>
                                </Box>
                            ) :
                            /* --- Default message when nothing is selected --- */
                            !selectedSentence ? (
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                                    <Typography color="text.secondary">Select a sentence to begin.</Typography>
                                </Box>
                            ) : editingTag.isActive ? (
                              <Box>
                                <Typography variant="overline">EDIT TAG</Typography>
                                <TextField 
                                label="Editable Tag Text" 
                                fullWidth 
                                variant="outlined" 
                                sx={{ my: 2 }} 
                                value={editingTag.text} 
                                onChange={(e) => setEditingTag(prev => ({ ...prev, text: e.target.value }))} 
                                />
                                
                                <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>Tag Label</InputLabel>
                                <Select
                                    value={editingTag.tag}
                                    label="Tag Label"
                                    onChange={(e) => setEditingTag(prev => ({ ...prev, tag: e.target.value }))}
                                >
                                    {PREDEFINED_TAGS.map((tag) => (
                                    <MenuItem key={tag} value={tag}>
                                        {tag}
                                    </MenuItem>
                                    ))}
                                </Select>
                                </FormControl>
                                
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button onClick={handleUpdateTag} variant="contained">Save Changes</Button>
                                <Button onClick={() => setEditingTag({ isActive: false, _id: null, text: '', tag: '' })} variant="outlined">Cancel</Button>
                                </Box>
                              </Box>
                            ) : newSelection.isActive ? (
                                <Box>
                                    <Typography variant="overline">CREATE NEW TAG</Typography>
                                    <TextField 
                                        label="Selected Text" 
                                        fullWidth 
                                        variant="outlined" 
                                        value={newSelection.text} 
                                        onChange={(e) => {
                                            setNewSelection(s => ({ ...s, text: e.target.value }));
                                            fetchTagRecommendations(e.target.value);
                                        }} 
                                        sx={{ my: 2 }} 
                                    />
                                    
                                    {showRecommendations && tagRecommendations.length > 0 && (
                                        <Box sx={{ mb: 2, p: 1, border: '1px solid #e0e0e0', borderRadius: 1, backgroundColor: '#f5f5f5' }}>
                                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                Recommended Tags:
                                            </Typography>
                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                {tagRecommendations.slice(0, 5).map((rec, index) => (
                                                    <Chip
                                                        key={index}
                                                        label={`${rec.recommended_tag} (${Math.round(rec.confidence * 100)}%)`}
                                                        onClick={() => handleSelectRecommendation(rec)}
                                                        color={rec.is_auto_detected ? "secondary" : "primary"}
                                                        variant={newSelection.tag === rec.recommended_tag ? "filled" : "outlined"}
                                                        sx={{ cursor: 'pointer' }}
                                                        title={
                                                            rec.is_auto_detected 
                                                                ? `Auto-detected: "${rec.phrase}"` 
                                                                : `Phrase: "${rec.phrase}" - Used ${rec.occurrence_count} times`
                                                        }
                                                    />
                                                ))}
                                            </Box>
                                            {tagRecommendations.some(rec => rec.is_auto_detected) && (
                                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                                    * Purple chips are auto-detected from existing annotations
                                                </Typography>
                                            )}
                                        </Box>
                                    )}

                                    
                                    {isLoadingRecommendations && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                            <CircularProgress size={20} sx={{ mr: 1 }} />
                                            <Typography variant="body2" color="text.secondary">
                                                Loading recommendations...
                                            </Typography>
                                        </Box>
                                    )}
                                    
                                    <FormControl fullWidth sx={{ mb: 2 }}>
                                        <InputLabel>Tag Label</InputLabel>
                                        <Select
                                            value={newSelection.tag}
                                            label="Tag Label"
                                            onChange={(e) => setNewSelection(s => ({ ...s, tag: e.target.value }))}
                                        >
                                            {PREDEFINED_TAGS.map((tag) => (
                                                <MenuItem key={tag} value={tag}>
                                                    {tag}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                    
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        <Button onClick={handleSaveNewTag} variant="contained">Save Tag</Button>
                                        <Button onClick={() => {
                                            setNewSelection({ isActive: false, text: '', tag: '' });
                                            setShowRecommendations(false);
                                            setTagRecommendations([]);
                                        }} variant="outlined">Cancel</Button>
                                    </Box>
                                </Box>
                            ) : (
                                <Box>
                                    <Typography variant="overline">TAGS FOR THIS SENTENCE</Typography> 
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
    {currentSentenceTags.map(tag => {
        const isHierarchical = isHierarchicalTag(tag.tag);
        const tagStatus = getTagStatus(tag);
        const isPendingReview = tagStatus === 'pending';
        
        // Tooltip content based on tag type
        const tooltipTitle = isHierarchical 
            ? `Named Entity Tag - Cannot be edited or deleted`
            : isPendingReview 
                ? `Pending review - Click to edit, X to delete`
                : `Approved - Annotated by: ${tag.username} - Click to edit, X to delete`;

        return (
            <Tooltip key={tag._id} title={tooltipTitle} arrow>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Chip 
                        label={
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                {tag.text} ({tag.tag})
                                {isHierarchical && (
                                    <Box sx={{ ml: 0.5, fontSize: '0.7rem', color: 'primary.main' }}>
                                        🔒
                                    </Box>
                                )}
                                {isPendingReview && (
                                    <Box sx={{ 
                                        ml: 1,
                                        width: 8, 
                                        height: 8, 
                                        borderRadius: '50%', 
                                        backgroundColor: '#ff9800',
                                        animation: 'pulse 1.5s infinite'
                                    }} />
                                )}
                            </Box>
                        }
                        onDelete={isHierarchical ? undefined : () => handleRemoveTag(tag._id)}
                        onClick={isHierarchical ? undefined : () => handleStartEditTag(tag)} 
                        color={isPendingReview ? "default" : "primary"}
                        variant={isPendingReview ? "outlined" : "filled"}
                        sx={{ 
                            cursor: isHierarchical ? "default" : "pointer",
                            border: isPendingReview ? '2px dashed #ff9800' : 'none',
                            position: 'relative',
                            opacity: isPendingReview ? 0.8 : 1,
                            backgroundColor: isHierarchical ? '#e3f2fd' : undefined,
                            '&:hover': {
                                backgroundColor: isHierarchical ? '#e3f2fd' : undefined,
                                transform: isHierarchical ? 'none' : 'scale(1.05)',
                            },
                            transition: 'all 0.2s ease-in-out',
                        }}
                    />
                    
                    {/* Individual Review Button */}
                    {!isHierarchical && tagStatus === 'approved' && (
                        <Tooltip title="Submit this tag for review">
                            <IconButton 
                                size="small" 
                                color="primary"
                                onClick={() => handleSubmitTagForReview(tag._id)}
                                sx={{ 
                                    bgcolor: 'primary.main',
                                    color: 'white',
                                    '&:hover': { bgcolor: 'primary.dark' }
                                }}
                            >
                                <RateReviewIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                    
                    {/* Cancel Review Button */}
                    {!isHierarchical && tagStatus === 'pending' && (
                        <Tooltip title="Cancel review request">
                            <IconButton 
                                size="small" 
                                color="warning"
                                onClick={() => handleCancelTagReview(tag._id)}
                                sx={{ 
                                    bgcolor: 'warning.main',
                                    color: 'white',
                                    '&:hover': { bgcolor: 'warning.dark' }
                                }}
                            >
                                <AssignmentLateIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>
            </Tooltip>
        );
    })}

    {currentSentenceTags.length === 0 && (
        <Typography color="text.secondary">No tags yet. Highlight text to add one.</Typography>
    )}
</Box>

                                    <Typography variant="overline" sx={{ mt: 3, display: 'block' }}>SENTENCE ACTIONS</Typography>
                                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                                        <Button 
                                            variant="contained" 
                                            color="success" 
                                            onClick={() => handleStatusChange(true)} 
                                            disabled={selectedSentence.is_annotated}
                                            sx={{
                                                '&.Mui-disabled': {
                                                    color: 'white',
                                                    backgroundColor: theme.palette.success.main,
                                                    opacity: 0.7
                                                },
                                                // --- NEW STYLING ---
                                                fontWeight: 'bold',
                                                boxShadow: theme.shadows[3],
                                                transition: 'transform 0.1s',
                                                '&:hover': { transform: 'scale(1.02)' },
                                                '&:active': { // <--- ADDED CLICK FEEDBACK
                                                    transform: 'translateY(1px)', 
                                                    boxShadow: 'none' 
                                                }
                                                // --- END NEW STYLING ---
                                            }}
                                        >
                                            Mark as Annotated
                                        </Button>
                                        <Button 
                                            variant="outlined" 
                                            color="secondary" 
                                            onClick={() => handleStatusChange(false)} 
                                            disabled={!selectedSentence.is_annotated}
                                            sx={{
                                                // --- NEW STYLING ---
                                                fontWeight: 'bold',
                                                boxShadow: theme.shadows[3],
                                                transition: 'transform 0.1s',
                                                '&:hover': { transform: 'scale(1.02)' },
                                                '&:active': { // <--- ADDED CLICK FEEDBACK
                                                    transform: 'translateY(1px)', 
                                                    boxShadow: 'none' 
                                                }
                                                // --- END NEW STYLING ---
                                            }}
                                        >
                                            Mark as Not Annotated
                                        </Button>

                                        </Box>
                                        
                                        {/* Alert for Submission Success/Error */}
                                        {reviewStatusMessage && (
                                            <Alert severity={reviewStatusMessage.severity} onClose={() => setReviewStatusMessage(null)} sx={{ mt: 2 }}>
                                                {reviewStatusMessage.message}
                                            </Alert>
                                        )}
                                </Box>
                            )}
                        </Box>
                    </Box>
                </Box>
            </Paper>

            <Dialog open={deleteConfirmation.isOpen} onClose={() => setDeleteConfirmation({ isOpen: false, sentenceId: null })}>
                <DialogTitle>Confirm Deletion</DialogTitle>
                <DialogContent>
                    <DialogContentText>Are you sure you want to delete this sentence? This action cannot be undone.</DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteConfirmation({ isOpen: false, sentenceId: null })} color="secondary">Cancel</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={bulkUploadDialog} onClose={() => setBulkUploadDialog(false)}>
                <DialogTitle>Bulk Upload Sentences</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Upload a .txt, .pdf, .doc, .docx, or .csv file with one sentence per line/paragraph/row.
                        Optionally, add a tag to apply to all sentences.
                    </DialogContentText>
                    <input
                        type="file"
                        accept=".txt,.pdf,.doc,.docx,.csv"
                        onChange={(e) => setFile(e.target.files[0])}
                        style={{ marginTop: '16px', marginBottom: '16px' }}
                    />
                    <TextField
                        fullWidth
                        label="Optional Tag (e.g., Concept/Noun)"
                        value={bulkTag}
                        onChange={(e) => setBulkTag(e.target.value)}
                        variant="outlined"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setBulkUploadDialog(false)} color="secondary">Cancel</Button>
                </DialogActions>
            </Dialog>

             <FeedbackDialog 
                open={isFeedbackOpen} 
                onClose={handleFeedbackClose} 
                userEmail={userData?.email || `${username}@placeholder.com`} 
            />

            <SentencesRevisionNotesDialog
                open={isRevisionNotesDialogOpen}
                onClose={() => setIsRevisionNotesDialogOpen(false)}
                username={username}
                onNavigateToSentence={handleNavigateToSentence}
                revisionNotes={revisionList}
            />

            <Dialog 
                open={statsDialogOpen} 
                onClose={() => setStatsDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    <Typography variant="h6" component="div">
                        Tag Database Statistics
                    </Typography>
                </DialogTitle>
                <DialogContent>
                    {isLoadingStats ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                            <CircularProgress />
                        </Box>
                    ) : tagStats ? (
                        <Box>
                            {/* Summary Section */}
                            <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
                                <Typography variant="h6" gutterBottom>
                                    Summary
                                </Typography>
                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <Typography variant="body2">
                                            <strong>Total Annotated Phrases:</strong> {tagStats.total_annotated_phrases}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="body2">
                                            <strong>Tag Types:</strong> {tagStats.tag_statistics?.length || 0}
                                        </Typography>
                                    </Grid>
                                </Grid>
                            </Paper>

                            {/* Tag Type Statistics */}
                            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                                Tag Type Distribution
                            </Typography>
                            {tagStats.tag_statistics && tagStats.tag_statistics.length > 0 ? (
                                <Box sx={{ mb: 3 }}>
                                    {tagStats.tag_statistics.map((stat, index) => (
                                        <Paper 
                                            key={stat.tag_type || index} 
                                            elevation={1} 
                                            sx={{ p: 2, mb: 1 }}
                                        >
                                            <Grid container spacing={2} alignItems="center">
                                                <Grid item xs={4}>
                                                    <Typography variant="subtitle1" fontWeight="bold">
                                                        {stat.tag_type || 'Unknown'}
                                                    </Typography>
                                                </Grid>
                                                <Grid item xs={3}>
                                                    <Typography variant="body2">
                                                        Total: {stat.total_annotations}
                                                    </Typography>
                                                </Grid>
                                                <Grid item xs={3}>
                                                    <Typography variant="body2">
                                                        Unique Phrases: {stat.unique_phrases_count}
                                                    </Typography>
                                                </Grid>
                                                <Grid item xs={2}>
                                                    <Chip 
                                                        label={stat.total_annotations} 
                                                        color="primary" 
                                                        size="small" 
                                                    />
                                                </Grid>
                                            </Grid>
                                            {stat.unique_phrases_count > 0 && (
                                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                                    Sample phrases: {stat.unique_phrases?.slice(0, 3).join(', ')}
                                                    {stat.unique_phrases_count > 3 && '...'}
                                                </Typography>
                                            )}
                                        </Paper>
                                    ))}
                                </Box>
                            ) : (
                                <Typography color="text.secondary" sx={{ mb: 2 }}>
                                    No tag statistics available.
                                </Typography>
                            )}

                            {/* Most Common Phrases */}
                            {tagStats.most_common_phrases && tagStats.most_common_phrases.length > 0 && (
                                <>
                                    <Typography variant="h6" gutterBottom>
                                        Most Common Phrases
                                    </Typography>
                                    <Paper elevation={1} sx={{ p: 2 }}>
                                        <Box sx={{ maxHeight: '200px', overflowY: 'auto' }}>
                                            {tagStats.most_common_phrases.map((phrase, index) => (
                                                <Box 
                                                    key={index} 
                                                    sx={{ 
                                                        display: 'flex', 
                                                        justifyContent: 'space-between', 
                                                        alignItems: 'center',
                                                        py: 1,
                                                        borderBottom: index < tagStats.most_common_phrases.length - 1 ? '1px solid #e0e0e0' : 'none'
                                                    }}
                                                >
                                                    <Typography variant="body2">
                                                        "{phrase.phrase}"
                                                    </Typography>
                                                    <Chip 
                                                        label={`${phrase.occurrence_count} times`} 
                                                        size="small" 
                                                        variant="outlined"
                                                    />
                                                </Box>
                                            ))}
                                        </Box>
                                    </Paper>
                                </>
                            )}

                            {/* Additional Statistics */}
                            {tagStats.summary && (
                                <Paper elevation={1} sx={{ p: 2, mt: 2, backgroundColor: '#e8f5e8' }}>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Database Overview
                                    </Typography>
                                    <Grid container spacing={1}>
                                        <Grid item xs={12}>
                                            <Typography variant="body2">
                                                <strong>Report Generated:</strong> {tagStats.summary.report_generated}
                                            </Typography>
                                        </Grid>
                                        {tagStats.summary.total_sentences && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2">
                                                    <strong>Total Sentences:</strong> {tagStats.summary.total_sentences}
                                                </Typography>
                                            </Grid>
                                        )}
                                        {tagStats.summary.annotated_sentences && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2">
                                                    <strong>Annotated Sentences:</strong> {tagStats.summary.annotated_sentences}
                                                </Typography>
                                            </Grid>
                                        )}
                                        {tagStats.summary.annotation_rate && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2">
                                                    <strong>Annotation Rate:</strong> {tagStats.summary.annotation_rate.toFixed(1)}%
                                                </Typography>
                                            </Grid>
                                        )}
                                        {tagStats.summary.total_annotations && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2">
                                                    <strong>Total Annotations:</strong> {tagStats.summary.total_annotations}
                                                </Typography>
                                            </Grid>
                                        )}
                                    </Grid>
                                </Paper>
                            )}
                        </Box>
                    ) : (
                        <Typography color="error" sx={{ p: 2, textAlign: 'center' }}>
                            Failed to load tag statistics.
                        </Typography>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setStatsDialogOpen(false)} color="primary">
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
}

