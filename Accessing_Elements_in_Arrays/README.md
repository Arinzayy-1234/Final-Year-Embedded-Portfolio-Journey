Accessing_Elements_in_Arrays

PROTEUS DESIGN PROJECT NAME -> Calculate_Functions

ARDUINO PROJECT: ARRAY ITERATION AND ASCII MAPPING
This sketch demonstrates fundamental C++ concepts for embedded systems, specifically focusing on two different methods to access and iterate over elements in a fixed-size character array (C-style string). It also illustrates the relationship between a character (char) and its numerical ASCII value.

CODE STRUCTURE AND COMPONENTS
arrayOne[6]: A fixed-size 'char' array initialized with "HELLO". The size of 6 includes the 5 letters plus the mandatory null terminator (\0).

void setup(): Initializes Serial communication at 9600 baud and executes the two primary iteration loops.

void loop(): Empty, as the demonstration logic runs only once in setup().

ITERATION METHOD 1: RANGE-BASED 'FOR' LOOP
This modern C++ loop provides a clean, concise way to iterate over every element in the collection.

Code Logic: For every 'character' in 'arrayOne', it prints the character, then prints its corresponding ASCII numerical value using the (int)character type cast.

Skill Demonstrated: Iterating over a collection without manually managing indices.

ITERATION METHOD 2: INDEX-BASED 'FOR' LOOP
This traditional C-style loop uses a counter variable (i) to access elements by their position (index).

Code Logic: The loop runs for i < 6 (indices 0 through 5) and prints each element directly.

Skill Demonstrated: Direct memory access using an index.

Important Note: The loop includes index 5, which holds the null terminator (\0). This prints as an invisible character but is crucial for C-style string handling.