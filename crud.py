import time
from typing import List, Dict
import asyncio
from models import Result, SpinStatistics
from mongo_db_handler import MongoDBHandler
from bson.json_util import dumps

mongodb_handler_results = MongoDBHandler()
mongodb_handler_max_multipliers = MongoDBHandler(collection_name="max_multipliers")

TOP_MULTIPLIERS_RESULTS_NUMBER = 5
subscribers = []


async def event_generator():
    queue = asyncio.Queue()
    subscribers.append(queue)
    try:
        while True:
            data = await queue.get()
            yield {
                "event": "winners_added",
                "data": data,
            }
    finally:
        subscribers.remove(queue)


def remove_in_progress_round(results: List[Result]):
    if 'winners' not in results[-1]:
        del results[-1]


def watch_changes():
    with mongodb_handler_results.collection.watch([{
        "$match": {
            "operationType": "update",
            "updateDescription.updatedFields.winners": {"$exists": True}
        }
    }]) as stream:
        for change in stream:
            print(f"[Watcher] Detected update with 'winners':", change)

            updated_doc = mongodb_handler_results.collection.find_one({"_id": change["documentKey"]["_id"]})
            if updated_doc:
                data = dumps(updated_doc)
                print("[Watcher] Sending to clients:", data)

                for queue in subscribers:
                    queue.put_nowait(data)


def fetch_game_history(game_id: str = None, spins_amount: int = 70) -> List[Result]:
    if game_id:
        query = {"result": game_id}
    else:
        query = {}
    docs = mongodb_handler_results.query_document(query)[-spins_amount:]
    remove_in_progress_round(docs)
    return [Result(**doc) for doc in docs]


def fetch_top_multipliers(hours: int) -> List[dict]:
    epoch_time_now = int(time.time() * 1000)
    time_delta = hours * 60 * 60 * 1000
    cutoff_epoch_ms = epoch_time_now - time_delta
    query = {"gameTime": {"$gte": cutoff_epoch_ms}}

    recent_docs = list(mongodb_handler_max_multipliers.collection.find(query))

    # Step 2: Sort by multiplier descending
    sorted_by_multiplier = sorted(
        recent_docs, key=lambda doc: doc.get("multiplier", 0), reverse=True
    )

    # Step 3: Take top N
    top_multiplier_wins = sorted_by_multiplier[:TOP_MULTIPLIERS_RESULTS_NUMBER]

    # Step 4: Build gameId -> multiplier map & ordered list of gameIds
    game_id_to_multiplier = {doc["gameId"]: doc["multiplier"] for doc in top_multiplier_wins}
    ordered_game_ids = [doc["gameId"] for doc in top_multiplier_wins]

    # Step 5: Fetch all matching results
    matching_results = list(
        mongodb_handler_results.collection.find({"gameId": {"$in": ordered_game_ids}})
    )

    # Step 6: Build gameId -> result doc map
    game_id_to_result = {doc["gameId"]: doc for doc in matching_results}

    # Step 7: Reconstruct ordered + merged output
    enriched_results = []
    for game_id in ordered_game_ids:
        result = game_id_to_result.get(game_id)
        if result:
            result["totalMultiplierHit"] = game_id_to_multiplier[game_id]
            enriched_results.append(result)

    return enriched_results


def find_recent_occurrences(limit=1000):
    target_results = ["1", "2", "5", "10", "b1", "b2", "b3", "b4"]
    pipeline = [
        {"$sort": {"_id": -1}},  # Most recent first
        {"$limit": limit},
        {"$project": {"result": 1}}
    ]

    docs = list(mongodb_handler_results.collection.aggregate(pipeline))

    occurrences = {}
    for result in target_results:
        occurrences[result] = None  # Default if not found

    for idx, doc in enumerate(docs):
        val = str(doc.get("result"))
        if val in occurrences and occurrences[val] is None:
            occurrences[val] = idx  # First time seen

        # Optional early stop: if all values found
        if all(v is not None for v in occurrences.values()):
            break

    return occurrences


def fetch_spin_statistics(spins_amount: int) -> List[SpinStatistics]:
    # Step 1: define all expected result types
    expected_results = ["1", "2", "5", "10", "b1", "b2", "b3", "b4"]

    # Step 2: run aggregation over last N documents with result
    pipeline = [
        {"$match": {"result": {"$exists": True, "$ne": None}}},
        {"$sort": {"_id": -1}},
        {"$limit": spins_amount},
        {"$group": {
            "_id": "$result",
            "count": {"$sum": 1}
        }}
    ]
    result_docs = list(mongodb_handler_results.collection.aggregate(pipeline))

    # Step 3: compute occurrences positions (how many spins ago each appeared)
    occurrences = find_recent_occurrences(spins_amount)

    # Step 4: build frequency map from aggregation
    frequency_map = {str(doc["_id"]): doc["count"] for doc in result_docs}

    # Step 5: return frequency + last occurrence for all expected types
    return [
        {
            "result": result,
            "frequency": round((frequency_map.get(result, 0) / spins_amount) * 100, 2),
            "lastOccurrence": occurrences.get(result, None)  # could be int or None
        }
        for result in expected_results
    ]


def fetch_topslot_rounds(spins_amount: int) -> List[Result]:
    query = {
        "$expr": {
            "$and": [
                {"$in": [{"$type": "$topSlot.result"}, ["string", "int"]]},
                {"$in": [{"$type": "$result"}, ["string", "int"]]},
                {"$ne": ["$topSlot.multiplier", "Miss"]},
                {"$eq": ["$topSlot.result", "$result"]}

            ]
        }
    }

    # sort by most recent (assuming _id or timestamp represents insertion order)
    results = list(mongodb_handler_results.collection.find(query).sort([("_id", -1)]).limit(spins_amount))
    return results
