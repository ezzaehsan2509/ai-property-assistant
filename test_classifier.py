from classifier import classify_question

while True:
    question = input("Enter your question: ")

    result = classify_question(question)

    print("Result:", result)