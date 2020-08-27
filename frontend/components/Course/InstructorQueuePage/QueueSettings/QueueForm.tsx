import React, { useState } from "react";
import { Form, Button, Modal } from "semantic-ui-react";
import Snackbar from "@material-ui/core/Snackbar";
import Alert from "@material-ui/lab/Alert";
import { Queue, mutateResourceListFunction } from "../../../../types";
import { logException } from "../../../../utils/sentry";

// TODO: error check PATCH
interface QueueFormProps {
    queue: Queue;
    mutate: mutateResourceListFunction<Queue>;
    backFunc: () => void;
}
const QueueForm = (props: QueueFormProps) => {
    const loading = false;
    /* STATE */
    const [success, setSuccess] = useState(false);
    const [disabled, setDisabled] = useState(true);
    const [error, setError] = useState(false);
    const { queue } = props;
    const [open, setOpen] = useState(false);
    const [input, setInput] = useState({
        name: queue.name,
        description: queue.description,
        queueId: queue.id,
    });
    const [nameCharCount, setNameCharCount] = useState(input.name.length);
    const [descCharCount, setDescCharCount] = useState(
        input.description.length
    );

    /* HANDLER FUNCTIONS */
    const handleInputChange = (e, { name, value }) => {
        if (name === "description" && value.length > 500) return;
        if (name === "name" && value.length > 100) return;
        input[name] = value;
        setInput(input);
        setDescCharCount(input.description.length);
        setNameCharCount(input.name.length);
        setDisabled(
            !input.name ||
                !input.description ||
                (input.name === queue.name &&
                    input.description === queue.description)
        );
    };

    const onSubmit = async () => {
        try {
            await props.mutate(queue.id, input);
            setSuccess(true);
            props.backFunc();
        } catch (e) {
            logException(e);
            setError(true);
        }
    };

    const onArchived = async () => {
        await props.mutate(queue.id, { archived: true });
        setOpen(false);
        props.backFunc();
    };

    /* PROPS UPDATE */

    return (
        <Form>
            {queue && (
                <div>
                    <Form.Field>
                        <label htmlFor="form-name">Name</label>
                        <Form.Input
                            id="form-name"
                            defaultValue={input.name}
                            name="name"
                            value={input.name}
                            disabled={loading}
                            onChange={handleInputChange}
                        />
                        <div
                            style={{
                                textAlign: "right",
                                color: nameCharCount < 100 ? "" : "crimson",
                            }}
                        >
                            {`Characters: ${nameCharCount}/100`}
                        </div>
                    </Form.Field>
                    <Form.Field>
                        <label htmlFor="form-desc">Description</label>
                        <Form.Input
                            id="form-desc"
                            defaultValue={input.description}
                            name="description"
                            value={input.description}
                            disabled={loading}
                            onChange={handleInputChange}
                        />
                        <div
                            style={{
                                textAlign: "right",
                                color: descCharCount < 500 ? "" : "crimson",
                            }}
                        >
                            {`Characters: ${descCharCount}/500`}
                        </div>
                    </Form.Field>
                    <Button
                        color="blue"
                        type="submit"
                        disabled={disabled || loading}
                        loading={loading}
                        onClick={onSubmit}
                    >
                        Save
                    </Button>
                    <Modal
                        open={open}
                        trigger={
                            <Button type="submit" onClick={() => setOpen(true)}>
                                Archive
                            </Button>
                        }
                    >
                        <Modal.Header>Archive Queue</Modal.Header>
                        <Modal.Content>
                            You are about to archive this queue:{" "}
                            <b>{queue.name}</b>.
                        </Modal.Content>
                        <Modal.Actions>
                            <Button
                                content="Cancel"
                                disabled={loading}
                                onClick={() => setOpen(false)}
                            />
                            <Button
                                content="Archive"
                                onClick={onArchived}
                                disabled={loading}
                                color="red"
                            />
                        </Modal.Actions>
                    </Modal>
                </div>
            )}
            <Snackbar
                open={success}
                autoHideDuration={2000}
                onClose={() => setSuccess(false)}
            >
                <Alert severity="success" onClose={() => setSuccess(false)}>
                    <span>
                        <b>{queue.name}</b> successfully updated
                    </span>
                </Alert>
            </Snackbar>
            <Snackbar
                open={error}
                autoHideDuration={6000}
                onClose={() => setError(false)}
            >
                <Alert severity="error" onClose={() => setError(false)}>
                    <span>
                        There was an error editing <b>{queue.name}</b>
                    </span>
                </Alert>
            </Snackbar>
        </Form>
    );
};

export default QueueForm;
