import React, { useState } from 'react';
import { Grid } from 'semantic-ui-react';
import StudentQueues from './StudentQueues';

import { gql } from 'apollo-boost';
import { useQuery } from '@apollo/react-hooks';
import { queueSortFunc } from "../../../utils";

/* GRAPHQL QUERIES/MUTATIONS */
const GET_QUEUES = gql`
  query GetQueues($id: ID!) {
    course(id: $id) {
      id
      videoChatEnabled
      requireVideoChatUrlOnQuestions
      queues(archived: false) {
        edges {
          node {
            id
            name
            description
            tags
            estimatedWaitTime
            activeOverrideTime
            archived
            numberActiveQuestions
          }
        }
      }
    }
  }
`;

const CURRENT_QUESTION = gql`
  query CurrentQuestion($courseId: ID!) {
    currentQuestion(courseId: $courseId) {
      id
      text
      tags
      videoChatUrl
      questionsAhead
      state
      timeAsked
      timeAnswered
      timeRejected
      timeStarted
      timeWithdrawn
      rejectedReason
      rejectedReasonOther
      rejectedBy {
        preferredName
      }
      answeredBy {
        preferredName
      }
      queue {
        id
      }
    }
  }
`;

const StudentQueuePage = (props) => {
  const getQueuesRes = useQuery(GET_QUEUES, {
    variables: {
      id: props.course.id
    },
    pollInterval: 10000 + Math.random() * 2000,
    skip: !props.course.id
  });

  const getQuestionRes = useQuery(CURRENT_QUESTION, {
    variables: {
      courseId: props.course.id
    },
    pollInterval: 5000 + Math.random() * 500,
    skip: !props.course.id
  });

  const [queues, setQueues] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);

  const loadQueues = (data) => {
    return data.course.queues.edges.map(item => {
      return {
        id: item.node.id,
        videoChatEnabled: data.course.videoChatEnabled,
        requireVideoChatUrlOnQuestions: data.course.requireVideoChatUrlOnQuestions,
        name: item.node.name,
        description: item.node.description,
        tags: item.node.tags,
        activeOverrideTime: item.node.activeOverrideTime,
        estimatedWaitTime: item.node.estimatedWaitTime,
        numberActiveQuestions: item.node.numberActiveQuestions
      };
    }).sort(queueSortFunc);
  };

  if (getQueuesRes.data && getQueuesRes.data.course) {
    const newQueues = loadQueues(getQueuesRes.data);
    if (JSON.stringify(newQueues) !== JSON.stringify(queues)) {
      setQueues(newQueues);
    }
  }

  if (getQuestionRes.data && getQuestionRes.data.currentQuestion) {
    const newCurrentQuestion = getQuestionRes.data.currentQuestion;
    if (JSON.stringify(newCurrentQuestion) !== JSON.stringify(currentQuestion)) {
      setCurrentQuestion(newCurrentQuestion);
    }
  }

  const shouldStopPolling = () => {
    return getQuestionRes.data && getQuestionRes.data.currentQuestion && 
    getQuestionRes.data.currentQuestion.state !== "ACTIVE" && getQuestionRes.data.currentQuestion.state !== "STARTED"
  }

  if (shouldStopPolling()) getQuestionRes.stopPolling();

  return (
    <Grid stackable>
      <StudentQueues
        queues={ queues }
        question={ currentQuestion }
        refetch={ () => { getQuestionRes.refetch(); getQueuesRes.refetch() } }
        startPolling={ getQuestionRes.startPolling }/>
    </Grid>
  );
};

export default StudentQueuePage;
