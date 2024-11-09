FAMILY_MEMBERS = ['Dad', 'Son', 'Mum']

EXERCISE_TYPES = {
    'pull_ups': {
        'measurements': ['reps', 'sets'],
        'description': 'Full range of motion pull ups',
        'valid_goals': ['max_reps', 'total_reps', 'sets_completed']
    },
    'push_ups': {
        'measurements': ['reps', 'sets'],
        'description': 'Standard push ups',
        'valid_goals': ['max_reps', 'total_reps', 'sets_completed']
    },
    'dips': {
        'measurements': ['reps', 'sets'],
        'description': 'Full range dips',
        'valid_goals': ['max_reps', 'total_reps', 'sets_completed']
    },
    'hangs': {
        'measurements': ['time', 'sets'],
        'description': 'Dead hangs from pull up bar (seconds)',
        'valid_goals': ['max_time', 'total_time', 'sets_completed']
    }
}

GOAL_TYPES = {
    'max_reps': {
        'description': 'Maximum repetitions in a single set',
        'unit': 'reps'
    },
    'total_reps': {
        'description': 'Total repetitions in a session',
        'unit': 'reps'
    },
    'max_time': {
        'description': 'Maximum time in a single set',
        'unit': 'seconds'
    },
    'total_time': {
        'description': 'Total time in a session',
        'unit': 'seconds'
    },
    'sets_completed': {
        'description': 'Number of sets completed',
        'unit': 'sets'
    }
}