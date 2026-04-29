// unity/NPCClient.cs
using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class NPCClient : MonoBehaviour
{
    [Serializable]
    public class Player
    {
        public int level;
        public int hp;
        public string[] inventory;
        public string[] completed_quests;
    }

    [Serializable]
    public class Tendencies
    {
        public float risk_taking;
        public float exploration;
        public float caution;
    }

    [Serializable]
    public class Behavior
    {
        public string[] recent_actions;
        public Tendencies tendencies;
    }

    [Serializable]
    public class World
    {
        public string location;
        public string time;          // "day" | "night" | etc.
        public string danger_level;  // "low" | "medium" | "high"
    }

    [Serializable]
    public class Story
    {
        public string chapter;
        public string active_objective;
        public string objective_state; // "not_started" | "in_progress" | "blocked" | "done"
        public int ignored_mainline_seconds;
    }

    [Serializable]
    public class Dialogue
    {
        public string[] last_npc_lines;
        public string[] last_player_lines;
        public int seconds_since_last_npc;
    }

    [Serializable]
    public class Memory
    {
        public string[] episodic_notes;
        public string[] semantic_summaries;
        public string[] long_term_traits;
    }

    [Serializable]
    public class NPC
    {
        public string name;
        public string role;
        public string personality;
        public string relationship;
    }

    [Serializable]
    public class NPCRequest
    {
        public Player player;
        public Behavior behavior;
        public World world;
        public Story story;
        public Dialogue dialogue;
        public Memory memory;
        public NPC npc;
    }

    [Serializable]
    public class NPCResponse
    {
        public string intent;
        public string dialogue;
        public string emotion;
        public string action;
        public string guidance;
        public string urgency_level;
        public string objective_reminder; // optional; may be null
        // reasoning_trace is complex structured data; omitted here (JsonUtility ignores unknown fields)
    }

    [Header("Endpoint")]
    public string serverUrl = "http://127.0.0.1:8089/npc";

    private void Start()
    {
        // Build a Step 3-compatible payload
        var req = new NPCRequest
        {
            player = new Player
            {
                level = 3,
                hp = 20,
                inventory = new[] { "sword", "herb" },
                completed_quests = new string[] { }
            },
            behavior = new Behavior
            {
                recent_actions = new[] { "explore_east", "attack_wolf", "use_herb", "inspect_ruins" },
                tendencies = new Tendencies { risk_taking = 0.6f, exploration = 0.7f, caution = 0.4f }
            },
            world = new World
            {
                location = "forest",
                time = "night",
                danger_level = "high"
            },
            story = new Story
            {
                chapter = "chapter_1",
                active_objective = "Reach the watchtower",
                objective_state = "in_progress",
                ignored_mainline_seconds = 180
            },
            dialogue = new Dialogue
            {
                last_npc_lines = new[] { "Stay close." },
                last_player_lines = new[] { "I'll scout ahead." },
                seconds_since_last_npc = 45
            },
            memory = new Memory
            {
                episodic_notes = new[] { "Warned player about wolves", "asked_for_hint" },
                semantic_summaries = new[] { "Player favors melee", "Avoid repeating wolf warning" },
                long_term_traits = new[] { "supportive_companion", "values_player_agency" }
            },
            npc = new NPC
            {
                name = "Elder Rowan",
                role = "healer",
                personality = "kind but cautious",
                relationship = "neutral"
            }
        };

        StartCoroutine(SendNPCRequest(req));
    }

    public IEnumerator SendNPCRequest(NPCRequest request)
    {
        string json = JsonUtility.ToJson(request);
        byte[] body = Encoding.UTF8.GetBytes(json);

        using (var uwr = new UnityWebRequest(serverUrl, "POST"))
        {
            uwr.uploadHandler = new UploadHandlerRaw(body);
            uwr.downloadHandler = new DownloadHandlerBuffer();
            uwr.SetRequestHeader("Content-Type", "application/json");

            yield return uwr.SendWebRequest();

#if UNITY_2020_1_OR_NEWER
            bool isError = uwr.result == UnityWebRequest.Result.ConnectionError ||
                           uwr.result == UnityWebRequest.Result.ProtocolError;
#else
            bool isError = uwr.isNetworkError || uwr.isHttpError;
#endif
            if (isError)
            {
                Debug.LogError($"NPC request failed: {uwr.responseCode} {uwr.error}\n{uwr.downloadHandler.text}");
                yield break;
            }

            string respText = uwr.downloadHandler.text;
            // Parse minimal schema fields
            NPCResponse resp = null;
            try
            {
                resp = JsonUtility.FromJson<NPCResponse>(respText);
            }
            catch (Exception ex)
            {
                Debug.LogError($"Failed to parse NPC response: {ex}\nRaw: {respText}");
                yield break;
            }

            if (resp != null)
            {
                Debug.Log($"NPC intent: {resp.intent}");
                Debug.Log($"Dialogue: {resp.dialogue}");
                Debug.Log($"Emotion: {resp.emotion}");
                Debug.Log($"Action: {resp.action}");
                Debug.Log($"Guidance: {resp.guidance}");
                Debug.Log($"Urgency: {resp.urgency_level}");
                if (!string.IsNullOrEmpty(resp.objective_reminder))
                {
                    Debug.Log($"Objective reminder: {resp.objective_reminder}");
                }
            }
            else
            {
                Debug.LogWarning("NPC response parsed to null object.");
            }
        }
    }
}
