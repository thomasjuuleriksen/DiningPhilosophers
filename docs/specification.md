I want to create a solution for dining philosophers problem.

Settings:
	#philosophers (shall be an integer bigger than 1)
	#max_eating_cycles (shall be an integer bigger than 1)
	#max_thinking_cycles (shall be an integer bigger than 1)
	#min_cycle_time (shall be an integer representing seconds and be bigger than 0)

Each philosopher shall be modeled as a separate thread.
	Each philosopher is given a number (for the queue) starting from 1
	A philosopher can think for a random period of 1 up to max_thinking_cycles, after which he needs to eat for a random period. Having eaten enough, he resumes thinking and the loop starts over
 	If a philosopher has not had the possibility to eat when requested within max_eating_cycles * 2, he will die of starvation; i.e. he dies after max_eating_cycles * 2 unless he gets to eat then	
	After having eaten - regardless of whether done or not - this starvation timer is reset. He will get to eat again or get queued in the next cycle

The algorithm shall be as follows:
	A queue of hungry philosophers is maintained
	Central loop going through all philosophers in a cycle, starting with the queued ones (in queued order); each cycle shall take at least min_cycle_time
		If the philosopher is dead, break the program
		If the philosopher is eating or thinking, proceed to the next
		If the philosopher is hungry 
			If neither of the adjacent philosophers are eating AND (no adjacent philosopher is in front of him in the queue who has waited more then max_eating_cycles in the queue), he is granted the right to take the two forks and eat for a period of 1 up to max_eating_cycles after which he puts down the forks; even if he is not done eating. If he was in the queue, he is removed from the queue
			Otherwise, if not already in the queue, he is enqueued with a cycles_count set to 0
	cycles_count field of each entry in the queue is incremented with 1


I want a simple text-based graphical representation
	The round table
	The bowl in the middle of the table
	Philosophers evenly distributed around the table
		A hungry philosopher is marked with a yellow H
		An eating philosopher is marked with a green E
		A thinking philosopher is marked with a blue T
		A dead philosopher is marked with a red D
	The forks shall be shown as -€
	When a philosopher holds a fork it is close to him
	When neither of two neighbouring philosophers hold a fork, it is placed in the middle between them
	The queue is shown underneath the graphical representation

The user shall be able to break the program, which otherwise shall run indefinitely