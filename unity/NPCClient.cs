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
    public class World
    {
        public string location;
        public string time;
        public string danger_level;
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
    public class InputPayload
    {
        public Player player;
        public World world;
        public NPC npc;
    }

    [Serializable]
    public class Quest
    {
        public string title;
        public string objective;
        public string reward;
    }

    [Serializable]
    public class NPCResponse
    {
        public string intent;
        public string dialogue;
        public string emotion;
        public string action;
        public Quest quest; // may be null
    }

    public string serverHost = "http://127.0.0.1:8089/npc";

    public IEnumerator SendNPCRequest(InputPayload payload, Action<NPCResponse> onSuccess, Action<string> onError)
    {
        string json = JsonUtility.ToJson(payload);
        using (UnityWebRequest www = new UnityWebRequest(serverHost, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");

            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                onError?.Invoke(www.error);
            }
            else
            {
                try
                {
                    NPCResponse resp = JsonUtility.FromJson<NPCResponse>(www.downloadHandler.text);
                    onSuccess?.Invoke(resp);
                }
                catch (Exception ex)
                {
                    onError?.Invoke($"JSON parse error: {ex.Message}\nRaw: {www.downloadHandler.text}");
                }
            }
        }
    }

    // Example usage
    void Start()
    {
        var payload = new InputPayload
        {
            player = new Player { level = 3, hp = 20, inventory = new[] { "sword", "herb" }, completed_quests = new string[] { } },
            world = new World { location = "forest", time = "night", danger_level = "high" },
            npc = new NPC { name = "Elder Rowan", role = "healer", personality = "kind but cautious", relationship = "neutral" }
        };
        StartCoroutine(SendNPCRequest(payload,
            onSuccess: (resp) => {
                Debug.Log($"NPC Intent: {resp.intent}\nDialogue: {resp.dialogue}\nEmotion: {resp.emotion}\nAction: {resp.action}\nQuest: {(resp.quest != null ? resp.quest.title : "none")} ");
            },
            onError: (err) => Debug.LogError($"NPC request failed: {err}")
        ));
    }
}
